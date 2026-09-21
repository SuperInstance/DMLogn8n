/**
 * Guild Halls and Strongholds System
 * Manages guild halls, upgrades, decorations, and facilities
 */

class GuildHalls {
    constructor(databaseClient, inventoryService, notificationService) {
        this.db = databaseClient;
        this.inventory = inventoryService;
        this.notifications = notificationService;
        this.hallCache = new Map();
    }

    /**
     * Get guild hall information
     */
    async getGuildHall(guildId) {
        try {
            // Check cache first
            if (this.hallCache.has(guildId)) {
                return this.hallCache.get(guildId);
            }

            const hall = await this.db.collection('guild_halls').findOne({ guildId: guildId });
            if (hall) {
                this.hallCache.set(guildId, hall);
            }
            return hall;
        } catch (error) {
            console.error('Error fetching guild hall:', error);
            return null;
        }
    }

    /**
     * Create initial guild hall
     */
    async createGuildHall(guildId, location, hallType = 'basic') {
        try {
            // Check if guild already has a hall
            const existingHall = await this.getGuildHall(guildId);
            if (existingHall) {
                throw new Error('Guild already has a hall');
            }

            // Get hall template
            const hallTemplate = this.getHallTemplate(hallType);
            if (!hallTemplate) {
                throw new Error('Invalid hall type');
            }

            // Create hall record
            const hall = {
                id: this.generateHallId(),
                guildId: guildId,
                name: `${guildId}'s Hall`,
                type: hallType,
                location: location,
                level: 1,
                experience: 0,
                rooms: hallTemplate.rooms,
                decorations: [],
                facilities: hallTemplate.facilities,
                storage: {
                    gold: 0,
                    resources: {},
                    items: []
                },
                upgrades: {
                    current: [],
                    available: hallTemplate.availableUpgrades
                },
                settings: {
                    publicAccess: false,
                    visitorPermissions: [],
                    teleportEnabled: false,
                    maintenanceCost: hallTemplate.maintenanceCost
                },
                status: 'active',
                created: new Date().toISOString(),
                lastModified: new Date().toISOString(),
                lastMaintenance: new Date().toISOString()
            };

            // Save to database
            await this.db.collection('guild_halls').insertOne(hall);

            // Initialize hall maintenance schedule
            await this.scheduleMaintenance(hall.id);

            // Update cache
            this.hallCache.set(guildId, hall);

            // Notify guild
            await this.notifyGuild(guildId, {
                type: 'hall_created',
                hallId: hall.id,
                location: location,
                hallType: hallType
            });

            return {
                success: true,
                hall: hall
            };

        } catch (error) {
            console.error('Error creating guild hall:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Upgrade guild hall
     */
    async upgradeHall(guildId, playerId, upgradeType) {
        try {
            // Get guild hall
            const hall = await this.getGuildHall(guildId);
            if (!hall) {
                throw new Error('Guild hall not found');
            }

            // Check permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'manage_hall')) {
                throw new Error('No permission to upgrade guild hall');
            }

            // Get upgrade details
            const upgrade = await this.getUpgradeDetails(upgradeType);
            if (!upgrade) {
                throw new Error('Invalid upgrade type');
            }

            // Check if upgrade is available
            if (!hall.upgrades.available.includes(upgradeType)) {
                throw new Error('Upgrade not available');
            }

            // Check if already upgraded
            if (hall.upgrades.current.includes(upgradeType)) {
                throw new Error('Upgrade already applied');
            }

            // Check requirements
            const requirements = await this.checkUpgradeRequirements(hall, upgrade);
            if (!requirements.met) {
                throw new Error(requirements.reason);
            }

            // Process upgrade
            await this.processUpgrade(hall, upgrade, playerId);

            // Apply upgrade effects
            await this.applyUpgradeEffects(hall, upgrade);

            // Update hall
            hall.upgrades.current.push(upgradeType);
            hall.level += upgrade.levelBonus || 1;
            hall.lastModified = new Date().toISOString();

            await this.db.collection('guild_halls').updateOne(
                { guildId: guildId },
                {
                    $push: { 'upgrades.current': upgradeType },
                    $inc: { level: upgrade.levelBonus || 1 },
                    $set: { lastModified: new Date().toISOString() }
                }
            );

            // Update cache
            this.hallCache.set(guildId, hall);

            // Notify guild
            await this.notifyGuild(guildId, {
                type: 'hall_upgraded',
                upgradeType: upgradeType,
                upgradedBy: playerId,
                newLevel: hall.level
            });

            return {
                success: true,
                hall: hall,
                upgrade: upgrade
            };

        } catch (error) {
            console.error('Error upgrading hall:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Add decoration to guild hall
     */
    async addDecoration(guildId, playerId, decorationData) {
        try {
            const {
                itemId,
                position,
                rotation,
                room = 'main',
                description = ''
            } = decorationData;

            // Get guild hall
            const hall = await this.getGuildHall(guildId);
            if (!hall) {
                throw new Error('Guild hall not found');
            }

            // Check permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'decorate_hall')) {
                throw new Error('No permission to decorate guild hall');
            }

            // Get item data
            const itemData = await this.inventory.getItemData(itemId);
            if (!itemData || !itemData.isDecoration) {
                throw new Error('Item is not a decoration');
            }

            // Check if player has the item
            const playerItem = await this.inventory.getPlayerItem(playerId, itemId);
            if (!playerItem || playerItem.quantity < 1) {
                throw new Error('Decoration item not found');
            }

            // Validate position
            if (!this.validatePosition(hall, room, position)) {
                throw new Error('Invalid decoration position');
            }

            // Remove item from player inventory
            await this.inventory.removePlayerItem(playerId, itemId, 1);

            // Add decoration to hall
            const decoration = {
                id: this.generateDecorationId(),
                itemId: itemId,
                name: itemData.name,
                description: description,
                position: position,
                rotation: rotation,
                room: room,
                placedBy: playerId,
                placedAt: new Date().toISOString()
            };

            await this.db.collection('guild_halls').updateOne(
                { guildId: guildId },
                {
                    $push: { decorations: decoration },
                    $set: { lastModified: new Date().toISOString() }
                }
            );

            // Update cache
            hall.decorations.push(decoration);
            this.hallCache.set(guildId, hall);

            // Notify guild
            await this.notifyGuild(guildId, {
                type: 'decoration_added',
                decoration: decoration,
                placedBy: playerId
            });

            return {
                success: true,
                decoration: decoration
            };

        } catch (error) {
            console.error('Error adding decoration:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Remove decoration from guild hall
     */
    async removeDecoration(guildId, playerId, decorationId) {
        try {
            // Get guild hall
            const hall = await this.getGuildHall(guildId);
            if (!hall) {
                throw new Error('Guild hall not found');
            }

            // Find decoration
            const decoration = hall.decorations.find(d => d.id === decorationId);
            if (!decoration) {
                throw new Error('Decoration not found');
            }

            // Check permissions
            const member = await this.getGuildMember(guildId, playerId);
            const canRemove = this.hasPermission(member, 'manage_hall') ||
                             decoration.placedBy === playerId;

            if (!canRemove) {
                throw new Error('No permission to remove this decoration');
            }

            // Return item to player (if not consumed)
            const itemData = await this.inventory.getItemData(decoration.itemId);
            if (itemData.returnable) {
                await this.inventory.addPlayerItem(playerId, decoration.itemId, 1);
            }

            // Remove decoration
            await this.db.collection('guild_halls').updateOne(
                { guildId: guildId },
                {
                    $pull: { decorations: { id: decorationId } },
                    $set: { lastModified: new Date().toISOString() }
                }
            );

            // Update cache
            hall.decorations = hall.decorations.filter(d => d.id !== decorationId);
            this.hallCache.set(guildId, hall);

            // Notify guild
            await this.notifyGuild(guildId, {
                type: 'decoration_removed',
                decorationId: decorationId,
                removedBy: playerId
            });

            return {
                success: true
            };

        } catch (error) {
            console.error('Error removing decoration:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Add facility to guild hall
     */
    async addFacility(guildId, playerId, facilityType, position) {
        try {
            // Get guild hall
            const hall = await this.getGuildHall(guildId);
            if (!hall) {
                throw new Error('Guild hall not found');
            }

            // Check permissions
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.hasPermission(member, 'manage_hall')) {
                throw new Error('No permission to manage guild hall');
            }

            // Get facility details
            const facility = this.getFacilityDetails(facilityType);
            if (!facility) {
                throw new Error('Invalid facility type');
            }

            // Check if facility already exists
            if (hall.facilities.some(f => f.type === facilityType)) {
                throw new Error('Facility already exists');
            }

            // Check requirements
            const requirements = await this.checkFacilityRequirements(hall, facility);
            if (!requirements.met) {
                throw new Error(requirements.reason);
            }

            // Process payment
            if (facility.cost) {
                await this.processFacilityPayment(guildId, facility.cost);
            }

            // Add facility
            const newFacility = {
                id: this.generateFacilityId(),
                type: facilityType,
                name: facility.name,
                description: facility.description,
                position: position,
                level: 1,
                uses: 0,
                maxUses: facility.maxUses || 1000,
                lastReset: new Date().toISOString(),
                builtBy: playerId,
                builtAt: new Date().toISOString()
            };

            await this.db.collection('guild_halls').updateOne(
                { guildId: guildId },
                {
                    $push: { facilities: newFacility },
                    $set: { lastModified: new Date().toISOString() }
                }
            );

            // Update cache
            hall.facilities.push(newFacility);
            this.hallCache.set(guildId, hall);

            // Notify guild
            await this.notifyGuild(guildId, {
                type: 'facility_added',
                facility: newFacility,
                builtBy: playerId
            });

            return {
                success: true,
                facility: newFacility
            };

        } catch (error) {
            console.error('Error adding facility:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Use facility
     */
    async useFacility(guildId, playerId, facilityId, options = {}) {
        try {
            // Get guild hall
            const hall = await this.getGuildHall(guildId);
            if (!hall) {
                throw new Error('Guild hall not found');
            }

            // Find facility
            const facility = hall.facilities.find(f => f.id === facilityId);
            if (!facility) {
                throw new Error('Facility not found');
            }

            // Check if facility has uses remaining
            if (facility.uses >= facility.maxUses) {
                throw new Error('Facility has reached maximum uses');
            }

            // Check permissions for facility use
            const member = await this.getGuildMember(guildId, playerId);
            if (!this.canUseFacility(member, facility)) {
                throw new Error('No permission to use this facility');
            }

            // Process facility use
            const result = await this.processFacilityUse(facility, playerId, options);

            // Update facility usage
            await this.db.collection('guild_halls').updateOne(
                {
                    guildId: guildId,
                    'facilities.id': facilityId
                },
                {
                    $inc: { 'facilities.$.uses': 1 },
                    $set: {
                        'facilities.$.lastUsed': new Date().toISOString(),
                        lastModified: new Date().toISOString()
                    }
                }
            );

            // Update cache
            facility.uses += 1;
            facility.lastUsed = new Date().toISOString();
            this.hallCache.set(guildId, hall);

            return {
                success: true,
                result: result,
                facility: facility
            };

        } catch (error) {
            console.error('Error using facility:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Process daily maintenance
     */
    async processMaintenance(guildId) {
        try {
            const hall = await this.getGuildHall(guildId);
            if (!hall) {
                throw new Error('Guild hall not found');
            }

            // Calculate maintenance cost
            const baseCost = hall.settings.maintenanceCost || 100;
            const upgradeCost = hall.upgrades.current.length * 20;
            const facilityCost = hall.facilities.length * 15;
            const totalCost = baseCost + upgradeCost + facilityCost;

            // Check if guild can afford maintenance
            const guildBank = await this.getGuildBank(guildId);
            if (guildBank.gold < totalCost) {
                // Hall enters degraded state
                await this.degradeHall(hall);
                return {
                    success: false,
                    reason: 'Insufficient funds for maintenance',
                    cost: totalCost
                };
            }

            // Pay maintenance
            await this.payMaintenance(guildId, totalCost);

            // Reset facility uses
            await this.resetFacilityUses(hall);

            // Update maintenance timestamp
            await this.db.collection('guild_halls').updateOne(
                { guildId: guildId },
                {
                    $set: {
                        lastMaintenance: new Date().toISOString(),
                        lastModified: new Date().toISOString()
                    }
                }
            );

            // Update cache
            hall.lastMaintenance = new Date().toISOString();
            this.hallCache.set(guildId, hall);

            // Notify guild leadership
            await this.notifyOfficers(guildId, {
                type: 'maintenance_paid',
                cost: totalCost,
                nextDue: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
            });

            return {
                success: true,
                cost: totalCost
            };

        } catch (error) {
            console.error('Error processing maintenance:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get hall visitors and access logs
     */
    async getHallVisitors(guildId, options = {}) {
        try {
            const {
                startDate = null,
                endDate = null,
                limit = 50,
                offset = 0
            } = options;

            let query = { guildId: guildId };

            if (startDate || endDate) {
                query.timestamp = {};
                if (startDate) {
                    query.timestamp.$gte = startDate;
                }
                if (endDate) {
                    query.timestamp.$lte = endDate;
                }
            }

            const visitors = await this.db.collection('guild_hall_visitors')
                .find(query)
                .sort({ timestamp: -1 })
                .skip(offset)
                .limit(limit)
                .toArray();

            return {
                success: true,
                visitors: visitors
            };

        } catch (error) {
            console.error('Error fetching hall visitors:', error);
            return {
                success: false,
                error: error.message,
                visitors: []
            };
        }
    }

    /**
     * Helper methods
     */
    generateHallId() {
        return 'hall_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateDecorationId() {
        return 'dec_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    generateFacilityId() {
        return 'fac_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    getHallTemplate(type) {
        const templates = {
            basic: {
                rooms: [
                    {
                        id: 'main',
                        name: 'Main Hall',
                        size: 'medium',
                        decorations: []
                    },
                    {
                        id: 'meeting',
                        name: 'Meeting Room',
                        size: 'small',
                        decorations: []
                    }
                ],
                facilities: [],
                availableUpgrades: ['expand_hall', 'add_storage', 'add_facilities'],
                maintenanceCost: 100
            },
            premium: {
                rooms: [
                    {
                        id: 'main',
                        name: 'Grand Hall',
                        size: 'large',
                        decorations: []
                    },
                    {
                        id: 'meeting',
                        name: 'Council Chamber',
                        size: 'medium',
                        decorations: []
                    },
                    {
                        id: 'training',
                        name: 'Training Grounds',
                        size: 'medium',
                        decorations: []
                    },
                    {
                        id: 'vault',
                        name: 'Guild Vault',
                        size: 'small',
                        decorations: []
                    }
                ],
                facilities: ['basic_vendor', 'message_board'],
                availableUpgrades: ['expand_hall', 'add_storage', 'add_facilities', 'teleport_pad'],
                maintenanceCost: 500
            }
        };

        return templates[type] || templates.basic;
    }

    getUpgradeDetails(upgradeType) {
        const upgrades = {
            expand_hall: {
                name: 'Expand Hall',
                description: 'Adds additional rooms to the guild hall',
                cost: { gold: 5000, resources: { wood: 100, stone: 100 } },
                requirements: { hallLevel: 2 },
                levelBonus: 1,
                effects: ['add_room']
            },
            add_storage: {
                name: 'Enhanced Storage',
                description: 'Increases guild bank capacity',
                cost: { gold: 3000 },
                requirements: { hallLevel: 1 },
                effects: ['increase_bank_capacity']
            },
            add_facilities: {
                name: 'Facility Slots',
                description: 'Allows construction of additional facilities',
                cost: { gold: 4000 },
                requirements: { hallLevel: 3 },
                effects: ['add_facility_slot']
            },
            teleport_pad: {
                name: 'Teleportation Pad',
                description: 'Enables guild-wide teleportation to hall',
                cost: { gold: 10000, resources: { crystal: 50 } },
                requirements: { hallLevel: 5 },
                effects: ['enable_teleport']
            }
        };

        return upgrades[upgradeType];
    }

    getFacilityDetails(facilityType) {
        const facilities = {
            basic_vendor: {
                name: 'Guild Vendor',
                description: 'Sells basic supplies to guild members',
                cost: { gold: 2000 },
                maxUses: 1000,
                permissions: ['members']
            },
            training_dummy: {
                name: 'Training Dummy',
                description: 'Practice combat skills',
                cost: { gold: 1500 },
                maxUses: 500,
                permissions: ['all']
            },
            enchanting_table: {
                name: 'Enchanting Table',
                description: 'Enchant equipment with guild bonuses',
                cost: { gold: 5000, resources: { crystal: 20 } },
                maxUses: 200,
                permissions: ['veterans']
            },
            message_board: {
                name: 'Message Board',
                description: 'Post guild announcements and quests',
                cost: { gold: 1000 },
                maxUses: -1, // Unlimited
                permissions: ['officers']
            },
            trophy_case: {
                name: 'Trophy Case',
                description: 'Display guild achievements and trophies',
                cost: { gold: 3000 },
                maxUses: -1,
                permissions: ['members']
            }
        };

        return facilities[facilityType];
    }

    hasPermission(member, permission) {
        const permissions = {
            'Leader': ['manage_hall', 'decorate_hall', 'use_facilities'],
            'Officer': ['decorate_hall', 'use_facilities'],
            'Veteran': ['decorate_hall', 'use_facilities'],
            'Member': ['use_facilities'],
            'Initiate': ['use_facilities']
        };

        return member && permissions[member.rank] &&
               permissions[member.rank].includes(permission);
    }

    canUseFacility(member, facility) {
        const facilityDetails = this.getFacilityDetails(facility.type);
        if (!facilityDetails) return false;

        const rankPermissions = {
            'Leader': true,
            'Officer': true,
            'Veteran': facilityDetails.permissions.includes('veterans') ||
                       facilityDetails.permissions.includes('members'),
            'Member': facilityDetails.permissions.includes('members'),
            'Initiate': facilityDetails.permissions.includes('all')
        };

        return rankPermissions[member.rank] || false;
    }

    validatePosition(hall, room, position) {
        // Check if room exists
        const roomData = hall.rooms.find(r => r.id === room);
        if (!roomData) return false;

        // Validate position format (x, y, z coordinates)
        if (!position.x || !position.y || !position.z) return false;

        // Check if position is within room bounds
        // This would involve more complex collision detection
        return true;
    }

    async checkUpgradeRequirements(hall, upgrade) {
        // Check hall level requirement
        if (upgrade.requirements && upgrade.requirements.hallLevel) {
            if (hall.level < upgrade.requirements.hallLevel) {
                return {
                    met: false,
                    reason: `Hall level ${upgrade.requirements.hallLevel} required`
                };
            }
        }

        // Check cost requirements
        if (upgrade.cost) {
            const guildBank = await this.getGuildBank(hall.guildId);

            if (upgrade.cost.gold && guildBank.gold < upgrade.cost.gold) {
                return {
                    met: false,
                    reason: `Insufficient gold: need ${upgrade.cost.gold}`
                };
            }

            // Check resource requirements
            if (upgrade.cost.resources) {
                for (const [resource, amount] of Object.entries(upgrade.cost.resources)) {
                    if (hall.storage.resources[resource] < amount) {
                        return {
                            met: false,
                            reason: `Insufficient ${resource}: need ${amount}`
                        };
                    }
                }
            }
        }

        return { met: true };
    }

    async checkFacilityRequirements(hall, facility) {
        return await this.checkUpgradeRequirements(hall, facility);
    }

    async processUpgrade(hall, upgrade, playerId) {
        // Deduct costs
        if (upgrade.cost) {
            if (upgrade.cost.gold) {
                await this.deductBankGold(hall.guildId, upgrade.cost.gold);
            }

            if (upgrade.cost.resources) {
                for (const [resource, amount] of Object.entries(upgrade.cost.resources)) {
                    hall.storage.resources[resource] -= amount;
                }
            }
        }
    }

    async processFacilityPayment(guildId, cost) {
        if (cost.gold) {
            await this.deductBankGold(guildId, cost.gold);
        }
    }

    async applyUpgradeEffects(hall, upgrade) {
        // Apply upgrade effects based on type
        if (upgrade.effects.includes('add_room')) {
            // Add new room to hall
            const newRoom = {
                id: 'room_' + Date.now(),
                name: 'New Room',
                size: 'small',
                decorations: []
            };
            hall.rooms.push(newRoom);
        }

        if (upgrade.effects.includes('increase_bank_capacity')) {
            // Increase bank capacity
            await this.increaseBankCapacity(hall.guildId, 50);
        }

        if (upgrade.effects.includes('enable_teleport')) {
            // Enable teleportation
            hall.settings.teleportEnabled = true;
        }
    }

    async processFacilityUse(facility, playerId, options) {
        const facilityDetails = this.getFacilityDetails(facility.type);

        switch (facility.type) {
            case 'basic_vendor':
                return await this.useGuildVendor(playerId, options);
            case 'training_dummy':
                return await this.useTrainingDummy(playerId, options);
            case 'enchanting_table':
                return await this.useEnchantingTable(playerId, options);
            case 'message_board':
                return await this.useMessageBoard(playerId, options);
            default:
                return { success: true, message: 'Facility used' };
        }
    }

    async useGuildVendor(playerId, options) {
        // Guild vendor logic - sell items at discount
        return { success: true, discount: 0.1 };
    }

    async useTrainingDummy(playerId, options) {
        // Training dummy logic - gain combat experience
        return { success: true, experience: 10 };
    }

    async useEnchantingTable(playerId, options) {
        // Enchanting table logic - enchant items
        return { success: true, enchantment: 'guild_blessing' };
    }

    async useMessageBoard(playerId, options) {
        // Message board logic - post messages
        return { success: true, message: 'Message posted' };
    }

    async degradeHall(hall) {
        // Hall enters degraded state
        await this.db.collection('guild_halls').updateOne(
            { guildId: hall.guildId },
            {
                $set: {
                    status: 'degraded',
                    lastModified: new Date().toISOString()
                }
            }
        );

        await this.notifyOfficers(hall.guildId, {
            type: 'hall_degraded',
            reason: 'Maintenance not paid'
        });
    }

    async resetFacilityUses(hall) {
        for (const facility of hall.facilities) {
            facility.uses = 0;
            facility.lastReset = new Date().toISOString();
        }

        await this.db.collection('guild_halls').updateOne(
            { guildId: hall.guildId },
            {
                $set: {
                    'facilities.$[].uses': 0,
                    'facilities.$[].lastReset': new Date().toISOString()
                }
            }
        );
    }

    async scheduleMaintenance(hallId) {
        // Schedule daily maintenance (would use a job scheduler)
        console.log(`Maintenance scheduled for hall ${hallId}`);
    }

    async payMaintenance(guildId, amount) {
        await this.deductBankGold(guildId, amount);
    }

    async deductBankGold(guildId, amount) {
        await this.db.collection('guild_banks').updateOne(
            { guildId: guildId },
            { $inc: { gold: -amount } }
        );
    }

    async increaseBankCapacity(guildId, additionalSlots) {
        await this.db.collection('guild_banks').updateOne(
            { guildId: guildId },
            {
                $inc: { 'tabs.$[].maxSlots': additionalSlots }
            }
        );
    }

    async getGuildBank(guildId) {
        return await this.db.collection('guild_banks').findOne({ guildId: guildId });
    }

    async getGuildMember(guildId, playerId) {
        return await this.db.collection('guild_members').findOne({
            guildId: guildId,
            playerId: playerId
        });
    }

    async notifyGuild(guildId, message) {
        await this.notifications.sendGuildNotification(guildId, message);
    }

    async notifyOfficers(guildId, message) {
        const officers = await this.db.collection('guild_members').find({
            guildId: guildId,
            rank: { $in: ['Leader', 'Officer'] }
        }).toArray();

        for (const officer of officers) {
            await this.notifications.sendPlayerNotification(officer.playerId, message);
        }
    }
}

module.exports = GuildHalls;