/**
 * Social Features System for Advanced Crafting
 * Handles crafting orders, guild workshops, competitions, and master-apprentice relationships
 */

class SocialFeatures {
    constructor(craftingSystem, materialSystem) {
        this.craftingSystem = craftingSystem;
        this.materialSystem = materialSystem;

        this.craftingOrders = new Map();
        this.guildWorkshops = new Map();
        this.competitions = new Map();
        this.apprenticeships = new Map();
        this.reputations = new Map();
        this.marketplace = new Map();

        this.initializeSocialSystem();
    }

    /**
     * Initialize Social Features
     */
    initializeSocialSystem() {
        this.setupEventHandlers();
        this.initializeMarketplace();
        this.setupReputationSystem();
    }

    /**
     * Crafting Orders System
     */
    async createCraftingOrder(clientId, orderDetails) {
        const client = this.craftingSystem.getCrafter(clientId);
        if (!client) {
            throw new Error('Invalid client');
        }

        // Validate order details
        const validation = this.validateOrderDetails(orderDetails);
        if (!validation.valid) {
            throw new Error(`Order validation failed: ${validation.reason}`);
        }

        const order = {
            id: this.generateOrderId(),
            clientId: clientId,
            type: orderDetails.type, // 'individual', 'bulk', 'commission'
            priority: orderDetails.priority || 'normal', // 'low', 'normal', 'high', 'urgent'
            specifications: {
                items: orderDetails.items,
                quality: orderDetails.quality || 'standard',
                deadline: orderDetails.deadline,
                specialRequirements: orderDetails.specialRequirements || []
            },
            payment: {
                amount: orderDetails.payment.amount,
                currency: orderDetails.payment.currency || 'gold',
                method: orderDetails.payment.method, // 'upfront', 'on_delivery', 'milestones'
                escrow: orderDetails.payment.escrow || true
            },
            status: 'open',
            applicants: [],
            selectedCrafter: null,
            timeline: {
                createdAt: new Date().toISOString(),
                deadline: orderDetails.deadline,
                estimatedCompletion: null,
                milestones: []
            },
            reputation: {
                clientRating: null,
                crafterRating: null,
                feedback: null,
                disputes: []
            },
            communication: {
                messages: [],
                attachments: [],
                updates: []
            }
        };

        // Calculate escrow if required
        if (order.payment.escrow) {
            await this.setupEscrow(order);
        }

        this.craftingOrders.set(order.id, order);

        // Notify potential crafters
        await this.notifyPotentialCrafters(order);

        // Log order creation
        this.logOrderActivity(order.id, 'created', { clientId });

        return order;
    }

    async applyForOrder(crafterId, orderId, application) {
        const crafter = this.craftingSystem.getCrafter(crafterId);
        const order = this.craftingOrders.get(orderId);

        if (!crafter || !order) {
            throw new Error('Invalid crafter or order');
        }

        if (order.status !== 'open') {
            throw new Error('Order is no longer accepting applications');
        }

        // Validate crafter eligibility
        const eligibility = await this.validateCrafterEligibility(crafter, order);
        if (!eligibility.eligible) {
            throw new Error(`Crafter not eligible: ${eligibility.reason}`);
        }

        const applicationData = {
            id: this.generateApplicationId(),
            crafterId: crafterId,
            orderId: orderId,
            proposal: {
                estimatedTime: application.estimatedTime,
                qualityGuarantee: application.qualityGuarantee,
                totalCost: application.totalCost,
                approach: application.approach,
                samples: application.samples || []
            },
            qualifications: {
                skillLevel: crafter.skills,
                experience: crafter.stats,
                portfolio: application.portfolio || [],
                references: application.references || []
            },
            reputation: {
                overallRating: this.getCrafterReputation(crafterId).overall,
                completedOrders: this.getCrafterReputation(crafterId).completedOrders,
                reliability: this.getCrafterReputation(crafterId).reliability
            },
            status: 'pending',
            submittedAt: new Date().toISOString()
        };

        order.applicants.push(applicationData);
        this.craftingOrders.set(orderId, order);

        // Notify client of new application
        await this.notifyClientOfApplication(order.clientId, applicationData);

        return applicationData;
    }

    async acceptApplication(orderId, applicationId, clientId) {
        const order = this.craftingOrders.get(orderId);
        const application = order.applicants.find(app => app.id === applicationId);

        if (!order || !application) {
            throw new Error('Invalid order or application');
        }

        if (order.clientId !== clientId) {
            throw new Error('Only the client can accept applications');
        }

        // Update order status
        order.status = 'in_progress';
        order.selectedCrafter = application.crafterId;
        order.timeline.estimatedCompletion = this.calculateEstimatedCompletion(application.proposal.estimatedTime);

        // Notify selected crafter
        await this.notifyCrafterOfAcceptance(application.crafterId, order);

        // Notify other applicants
        await this.notifyRejectedApplicants(order.applicants.filter(app => app.id !== applicationId));

        this.craftingOrders.set(orderId, order);

        return { success: true, order: order };
    }

    /**
     * Guild Workshop Management
     */
    async createGuildWorkshop(guildId, workshopDetails) {
        const workshop = {
            id: this.generateWorkshopId(),
            guildId: guildId,
            name: workshopDetails.name,
            type: workshopDetails.type, // 'blacksmithing', 'alchemy', 'enchanting', 'mixed'
            level: 1,
            location: workshopDetails.location,
            resources: workshopDetails.initialResources || 1000,
            facilities: workshopDetails.facilities || [],
            equipment: workshopDetails.equipment || [],
            members: workshopDetails.foundingMembers || [],
            permissions: this.setupDefaultPermissions(),
            upgrades: [],
            bonuses: this.calculateWorkshopBonuses(workshopDetails.type, 1),
            activities: [],
            reputation: {
                rating: 5.0,
                reviews: [],
                achievements: []
            },
            economy: {
                dailyIncome: 0,
                expenses: 0,
                investments: [],
                profits: []
            },
            createdAt: new Date().toISOString(),
            status: 'active'
        };

        this.guildWorkshops.set(workshop.id, workshop);

        // Initialize workshop activities
        await this.initializeWorkshopActivities(workshop);

        return workshop;
    }

    async upgradeWorkshop(workshopId, upgradeType, resources) {
        const workshop = this.guildWorkshops.get(workshopId);
        if (!workshop) {
            throw new Error('Workshop not found');
        }

        const upgradeCost = this.calculateUpgradeCost(workshop, upgradeType);
        if (workshop.resources < upgradeCost) {
            throw new Error('Insufficient resources for upgrade');
        }

        // Apply upgrade
        workshop.resources -= upgradeCost;
        workshop.level += 1;

        if (upgradeType === 'facility') {
            workshop.facilities.push(upgradeType);
        } else if (upgradeType === 'equipment') {
            workshop.equipment.push(upgradeType);
        }

        workshop.bonuses = this.calculateWorkshopBonuses(workshop.type, workshop.level);
        workshop.upgrades.push({
            type: upgradeType,
            level: workshop.level,
            cost: upgradeCost,
            timestamp: new Date().toISOString()
        });

        this.guildWorkshops.set(workshopId, workshop);

        return { success: true, workshop: workshop };
    }

    async manageWorkshopAccess(workshopId, memberId, accessLevel) {
        const workshop = this.guildWorkshops.get(workshopId);
        if (!workshop) {
            throw new Error('Workshop not found');
        }

        const memberIndex = workshop.members.findIndex(m => m.id === memberId);
        if (memberIndex === -1) {
            throw new Error('Member not found in workshop');
        }

        workshop.members[memberIndex].accessLevel = accessLevel;
        workshop.members[memberIndex].lastUpdated = new Date().toISOString();

        this.guildWorkshops.set(workshopId, workshop);

        return { success: true, workshop: workshop };
    }

    /**
     * Crafting Competitions
     */
    async createCompetition(organizerId, competitionDetails) {
        const organizer = this.craftingSystem.getCrafter(organizerId);
        if (!organizer) {
            throw new Error('Invalid organizer');
        }

        const competition = {
            id: this.generateCompetitionId(),
            organizerId: organizerId,
            name: competitionDetails.name,
            description: competitionDetails.description,
            type: competitionDetails.type, // 'speed', 'quality', 'creativity', 'themed'
            category: competitionDetails.category, // 'blacksmithing', 'alchemy', etc.
            rules: competitionDetails.rules,
            judgingCriteria: competitionDetails.judgingCriteria,
            timeline: {
                registrationStart: competitionDetails.timeline.registrationStart,
                registrationEnd: competitionDetails.timeline.registrationEnd,
                competitionStart: competitionDetails.timeline.competitionStart,
                competitionEnd: competitionDetails.timeline.competitionEnd,
                announcement: competitionDetails.timeline.announcement
            },
            prizes: competitionDetails.prizes,
            entryFee: competitionDetails.entryFee || 0,
            maxParticipants: competitionDetails.maxParticipants || 50,
            participants: [],
            judges: competitionDetails.judges || [],
            submissions: {},
            scoring: {},
            status: 'registration',
            venue: competitionDetails.venue,
            requirements: competitionDetails.requirements || [],
            specialChallenges: competitionDetails.specialChallenges || [],
            createdAt: new Date().toISOString()
        };

        this.competitions.set(competition.id, competition);

        // Announce competition
        await this.announceCompetition(competition);

        return competition;
    }

    async registerForCompetition(competitionId, participantId, registrationData) {
        const competition = this.competitions.get(competitionId);
        const participant = this.craftingSystem.getCrafter(participantId);

        if (!competition || !participant) {
            throw new Error('Invalid competition or participant');
        }

        if (competition.status !== 'registration') {
            throw new Error('Registration is not open');
        }

        if (competition.participants.length >= competition.maxParticipants) {
            throw new Error('Competition is full');
        }

        // Validate registration requirements
        const validation = this.validateCompetitionRegistration(participant, competition);
        if (!validation.valid) {
            throw new Error(`Registration validation failed: ${validation.reason}`);
        }

        // Process entry fee
        if (competition.entryFee > 0) {
            await this.processEntryFee(participantId, competition.entryFee);
        }

        const registration = {
            participantId: participantId,
            registrationData: registrationData,
            registeredAt: new Date().toISOString(),
            status: 'confirmed'
        };

        competition.participants.push(registration);
        this.competitions.set(competitionId, competition);

        return { success: true, registration: registration };
    }

    async submitCompetitionEntry(competitionId, participantId, submission) {
        const competition = this.competitions.get(competitionId);

        if (!competition) {
            throw new Error('Competition not found');
        }

        if (competition.status !== 'active') {
            throw new Error('Competition is not active');
        }

        const entry = {
            participantId: participantId,
            submission: submission,
            submittedAt: new Date().toISOString(),
            status: 'submitted',
            preliminaryScore: null,
            finalScore: null,
            feedback: []
        };

        competition.submissions[participantId] = entry;

        // Initialize scoring
        competition.scoring[participantId] = {
            criteriaScores: {},
            totalScore: null,
            ranking: null
        };

        // Notify judges
        await this.notifyJudgesOfSubmission(competitionId, entry);

        this.competitions.set(competitionId, competition);

        return { success: true, entry: entry };
    }

    /**
     * Master-Apprentice System
     */
    async createApprenticeship(masterId, apprenticeId, terms) {
        const master = this.craftingSystem.getCrafter(masterId);
        const apprentice = this.craftingSystem.getCrafter(apprenticeId);

        if (!master || !apprentice) {
            throw new Error('Invalid master or apprentice');
        }

        // Validate apprenticeship requirements
        const validation = this.validateApprenticeshipRequirements(master, apprentice, terms);
        if (!validation.valid) {
            throw new Error(`Apprenticeship validation failed: ${validation.reason}`);
        }

        const apprenticeship = {
            id: this.generateApprenticeshipId(),
            masterId: masterId,
            apprenticeId: apprenticeId,
            terms: {
                duration: terms.duration, // in days
                specializations: terms.specializations || [],
                goals: terms.goals || [],
                obligations: terms.obligations || {},
                compensation: terms.compensation || {},
                terminationConditions: terms.terminationConditions || []
            },
            curriculum: this.generateCurriculum(terms.specializations),
            progress: {
                lessonsCompleted: 0,
                skillsLearned: [],
                itemsCrafted: 0,
                qualityImprovements: [],
                milestones: [],
                assessments: []
            },
            schedule: {
                sessions: [],
                milestones: [],
                assessments: []
            },
            status: 'active',
            startDate: new Date().toISOString(),
            endDate: new Date(Date.now() + terms.duration * 24 * 60 * 60 * 1000).toISOString(),
            evaluations: [],
            notes: [],
            achievements: []
        };

        this.apprenticeships.set(apprenticeship.id, apprenticeship);

        // Update crafter records
        master.apprentices = master.apprentices || [];
        master.apprentices.push(apprenticeId);
        apprentice.master = masterId;
        apprentice.apprenticeship = apprenticeship.id;

        // Generate initial curriculum
        await this.generateLearningSchedule(apprenticeship);

        return apprenticeship;
    }

    async conductTrainingSession(apprenticeshipId, sessionDetails) {
        const apprenticeship = this.apprenticeships.get(apprenticeshipId);
        if (!apprenticeship) {
            throw new Error('Apprenticeship not found');
        }

        const session = {
            id: this.generateSessionId(),
            apprenticeshipId: apprenticeshipId,
            type: sessionDetails.type, // 'lesson', 'practice', 'assessment', 'project'
            topic: sessionDetails.topic,
            description: sessionDetails.description,
            duration: sessionDetails.duration,
            materials: sessionDetails.materials || [],
            objectives: sessionDetails.objectives || [],
            outcomes: sessionDetails.outcomes || [],
            skillFocus: sessionDetails.skillFocus,
            scheduledAt: sessionDetails.scheduledAt || new Date().toISOString(),
            completedAt: null,
            results: {
                skillImprovement: {},
                itemsCreated: [],
                qualityAchieved: 0,
                notes: [],
                nextSteps: []
            },
            rating: null
        };

        apprenticeship.schedule.sessions.push(session);
        this.apprenticeships.set(apprenticeshipId, apprenticeship);

        return session;
    }

    /**
     * Reputation System
     */
    calculateReputation(crafterId, actionType, targetId, rating, feedback) {
        const reputation = this.reputations.get(crafterId) || {
            overall: 5.0,
            reliability: 5.0,
            quality: 5.0,
            communication: 5.0,
            professionalism: 5.0,
            completedOrders: 0,
            totalRatings: 0,
            recentRatings: [],
            achievements: [],
            penalties: []
        };

        // Add new rating
        const newRating = {
            actionType: actionType,
            targetId: targetId,
            rating: rating,
            feedback: feedback,
            timestamp: new Date().toISOString()
        };

        reputation.recentRatings.push(newRating);
        if (reputation.recentRatings.length > 100) {
            reputation.recentRatings.shift(); // Keep only last 100 ratings
        }

        // Update overall rating (weighted average)
        const weights = {
            'order_completion': 0.3,
            'crafting_quality': 0.25,
            'communication': 0.2,
            'timeliness': 0.15,
            'professionalism': 0.1
        };

        let totalScore = 0;
        let totalWeight = 0;

        reputation.recentRatings.forEach(rating => {
            const weight = weights[rating.actionType] || 0.1;
            totalScore += rating.rating * weight;
            totalWeight += weight;
        });

        reputation.overall = totalWeight > 0 ? totalScore / totalWeight : 5.0;

        // Update specific metrics
        this.updateReputationMetrics(reputation, actionType, rating);

        this.reputations.set(crafterId, reputation);

        return reputation;
    }

    /**
     * Marketplace Integration
     */
    async listMaterialOnMarketplace(sellerId, materialId, listingDetails) {
        const material = this.materialSystem.materials.get(materialId);
        if (!material) {
            throw new Error('Material not found');
        }

        const listing = {
            id: this.generateMarketplaceId(),
            sellerId: sellerId,
            materialId: materialId,
            type: 'material',
            listingType: listingDetails.type, // 'auction', 'fixed_price', 'trade'
            pricing: {
                startingPrice: listingDetails.pricing.startingPrice,
                buyoutPrice: listingDetails.pricing.buyoutPrice,
                currentBid: listingDetails.pricing.startingPrice,
                bidIncrement: listingDetails.pricing.bidIncrement || 5
            },
            quantity: listingDetails.quantity,
            quality: material.quality,
            duration: listingDetails.duration || 7 * 24 * 60 * 60 * 1000, // 7 days default
            description: listingDetails.description || '',
            tags: listingDetails.tags || [],
            status: 'active',
            views: 0,
            watchers: [],
            bids: [],
            history: [],
            createdAt: new Date().toISOString(),
            expiresAt: new Date(Date.now() + (listingDetails.duration || 7 * 24 * 60 * 60 * 1000)).toISOString()
        };

        this.marketplace.set(listing.id, listing);

        // Reserve material quantity
        material.quantity -= listing.quantity;

        return listing;
    }

    async bidOnMarketplaceListing(buyerId, listingId, bidAmount) {
        const listing = this.marketplace.get(listingId);
        if (!listing) {
            throw new Error('Listing not found');
        }

        if (listing.status !== 'active') {
            throw new Error('Listing is no longer active');
        }

        if (listing.pricing.currentBid >= bidAmount) {
            throw new Error('Bid must be higher than current bid');
        }

        const bid = {
            id: this.generateBidId(),
            buyerId: buyerId,
            amount: bidAmount,
            timestamp: new Date().toISOString(),
            status: 'active'
        };

        listing.bids.push(bid);
        listing.pricing.currentBid = bidAmount;

        // Notify previous high bidder
        if (listing.bids.length > 1) {
            const previousBid = listing.bids[listing.bids.length - 2];
            await this.notifyOutbid(previousBid.buyerId, listing);
        }

        this.marketplace.set(listingId, listing);

        return bid;
    }

    /**
     * Utility Methods
     */
    generateOrderId() {
        return 'order_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateApplicationId() {
        return 'app_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateWorkshopId() {
        return 'workshop_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateCompetitionId() {
        return 'comp_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateApprenticeshipId() {
        return 'apprentice_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateSessionId() {
        return 'session_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateMarketplaceId() {
        return 'listing_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    generateBidId() {
        return 'bid_' + Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    // Additional helper methods for validation, notifications, and calculations
    validateOrderDetails(orderDetails) {
        if (!orderDetails.items || orderDetails.items.length === 0) {
            return { valid: false, reason: 'Order must contain at least one item' };
        }
        if (!orderDetails.payment || !orderDetails.payment.amount) {
            return { valid: false, reason: 'Payment details are required' };
        }
        if (!orderDetails.deadline) {
            return { valid: false, reason: 'Deadline is required' };
        }
        return { valid: true };
    }

    getCrafterReputation(crafterId) {
        return this.reputations.get(crafterId) || {
            overall: 5.0,
            completedOrders: 0,
            reliability: 5.0
        };
    }

    calculateWorkshopBonuses(type, level) {
        const baseBonuses = {
            blacksmithing: { successChance: 0.1, quality: 1.1, speed: 1.2 },
            alchemy: { successChance: 0.15, potency: 1.2, duration: 1.3 },
            enchanting: { successChance: 0.12, power: 1.25, stability: 1.15 },
            mixed: { successChance: 0.08, quality: 1.05, versatility: 1.1 }
        };

        const bonuses = baseBonuses[type] || baseBonuses.mixed;
        const levelMultiplier = 1 + (level - 1) * 0.05;

        Object.keys(bonuses).forEach(key => {
            bonuses[key] *= levelMultiplier;
        });

        return bonuses;
    }

    setupEventHandlers() {
        // Set up event listeners for various social interactions
        this.craftingSystem.on('craftingCompleted', (data) => {
            this.handleCraftingCompletedEvent(data);
        });

        this.craftingSystem.on('skillLevelUp', (data) => {
            this.handleSkillLevelUpEvent(data);
        });
    }

    handleCraftingCompletedEvent(data) {
        // Update crafter reputation based on crafting results
        if (data.success && data.quality >= 80) {
            this.calculateReputation(data.crafterId, 'crafting_quality', data.recipeId, 5, 'High quality item crafted');
        }
    }

    handleSkillLevelUpEvent(data) {
        // Update achievement and reputation
        const reputation = this.reputations.get(data.crafterId);
        if (reputation) {
            reputation.achievements.push({
                type: 'skill_level_up',
                profession: data.profession,
                newLevel: data.newLevel,
                timestamp: new Date().toISOString()
            });
        }
    }
}

module.exports = SocialFeatures;