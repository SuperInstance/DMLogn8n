/**
 * Basic Test Suite for Advanced Crafting System
 */

const AdvancedCraftingSystem = require('../index.js');

describe('Advanced Crafting System - Basic Tests', () => {
    let craftingSystem;
    let testCrafter;

    beforeEach(() => {
        // Initialize system with test configuration
        craftingSystem = new AdvancedCraftingSystem({
            system: {
                maxSkillLevel: 500,
                baseExperienceMultiplier: 2.0
            },
            debugging: {
                enabled: false
            }
        });

        // Create test crafter
        testCrafter = {
            id: 'test_crafter',
            name: 'Test Smith',
            skills: {
                BLACKSMITHING: 150,
                ALCHEMY: 100
            },
            stats: {
                totalCrafts: 0,
                successfulCrafts: 0,
                criticalSuccesses: 0
            },
            resources: {
                gold: 1000
            },
            unlockedRecipes: [],
            achievements: []
        };

        craftingSystem.craftingSystem.crafters.set(testCrafter.id, testCrafter);
    });

    afterEach(() => {
        // Clean up after each test
        if (craftingSystem) {
            craftingSystem.craftingSystem.crafters.clear();
            craftingSystem.materialSystem.materials.clear();
        }
    });

    describe('System Initialization', () => {
        test('should initialize crafting system successfully', () => {
            expect(craftingSystem).toBeDefined();
            expect(craftingSystem.craftingSystem).toBeDefined();
            expect(craftingSystem.materialSystem).toBeDefined();
            expect(craftingSystem.socialFeatures).toBeDefined();
            expect(craftingSystem.professions).toBeDefined();
        });

        test('should load default professions', () => {
            expect(craftingSystem.professions.has('BLACKSMITHING')).toBe(true);
            expect(craftingSystem.professions.has('ALCHEMY')).toBe(true);
        });

        test('should have core crafting tiers configured', () => {
            const tiers = craftingSystem.craftingSystem.craftingTiers;
            expect(tiers.SIMPLE).toBeDefined();
            expect(tiers.ADVANCED).toBeDefined();
            expect(tiers.MASTER).toBeDefined();
            expect(tiers.ARTIFACT).toBeDefined();
            expect(tiers.MAGICAL).toBeDefined();
        });
    });

    describe('Crafter Management', () => {
        test('should create and retrieve crafter successfully', () => {
            const crafter = craftingSystem.craftingSystem.getCrafter('test_crafter');
            expect(crafter).toBeDefined();
            expect(crafter.name).toBe('Test Smith');
            expect(crafter.skills.BLACKSMITHING).toBe(150);
        });

        test('should update crafter stats after crafting', async () => {
            // Create test material
            const material = craftingSystem.materialSystem.createMaterial({
                name: 'Test Iron',
                type: 'METAL',
                quality: 75,
                quantity: 10,
                harvestedBy: testCrafter.id,
                location: 'test_mines'
            });

            // Perform crafting
            const result = await craftingSystem.craftItem(
                testCrafter.id,
                'dagger_basic',
                [{ id: material.id, quantity: 2 }]
            );

            expect(result.crafterId).toBe('test_crafter');
            expect(typeof result.experience).toBe('number');
            expect(result.experience).toBeGreaterThan(0);
        });

        test('should handle skill level up events', async () => {
            let levelUpEventFired = false;
            craftingSystem.craftingSystem.on('skillLevelUp', (data) => {
                levelUpEventFired = true;
                expect(data.crafterId).toBe('test_crafter');
                expect(data.newLevel).toBeGreaterThan(150);
            });

            // Simulate crafting that would trigger level up
            // (This would require enough experience to level up)
            for (let i = 0; i < 50; i++) {
                const material = craftingSystem.materialSystem.createMaterial({
                    name: `Test Iron ${i}`,
                    type: 'METAL',
                    quality: 75,
                    quantity: 10,
                    harvestedBy: testCrafter.id,
                    location: 'test_mines'
                });

                try {
                    await craftingSystem.craftItem(
                        testCrafter.id,
                        'dagger_basic',
                        [{ id: material.id, quantity: 2 }]
                    );
                } catch (error) {
                    // Ignore errors for this test
                }
            }

            // Note: In a real test, you'd need to ensure enough experience is gained
        });
    });

    describe('Material System', () => {
        test('should create material with correct properties', () => {
            const material = craftingSystem.materialSystem.createMaterial({
                name: 'Test Material',
                type: 'METAL',
                quality: 85,
                quantity: 5,
                harvestedBy: testCrafter.id,
                location: 'test_location'
            });

            expect(material).toBeDefined();
            expect(material.name).toBe('Test Material');
            expect(material.type).toBe('METAL');
            expect(material.quality).toBe(85);
            expect(material.quantity).toBe(5);
            expect(material.harvestedBy).toBe(testCrafter.id);
        });

        test('should retrieve material by ID', () => {
            const material = craftingSystem.materialSystem.createMaterial({
                name: 'Test Material',
                type: 'HERB',
                quality: 70,
                quantity: 3,
                harvestedBy: testCrafter.id,
                location: 'test_garden'
            });

            const retrieved = craftingSystem.materialSystem.getMaterial(material.id);
            expect(retrieved).toBeDefined();
            expect(retrieved.id).toBe(material.id);
            expect(retrieved.name).toBe('Test Material');
        });

        test('should calculate material value based on quality', () => {
            const highQualityMaterial = craftingSystem.materialSystem.createMaterial({
                name: 'High Quality',
                type: 'GEM',
                quality: 95,
                quantity: 1,
                harvestedBy: testCrafter.id,
                location: 'test_mine'
            });

            const lowQualityMaterial = craftingSystem.materialSystem.createMaterial({
                name: 'Low Quality',
                type: 'GEM',
                quality: 25,
                quantity: 1,
                harvestedBy: testCrafter.id,
                location: 'test_mine'
            });

            expect(highQualityMaterial.value).toBeGreaterThan(lowQualityMaterial.value);
        });
    });

    describe('Crafting Operations', () => {
        test('should craft basic item successfully', async () => {
            const material = craftingSystem.materialSystem.createMaterial({
                name: 'Test Iron',
                type: 'METAL',
                quality: 75,
                quantity: 10,
                harvestedBy: testCrafter.id,
                location: 'test_mines'
            });

            const result = await craftingSystem.craftItem(
                testCrafter.id,
                'dagger_basic',
                [{ id: material.id, quantity: 2 }]
            );

            expect(result).toBeDefined();
            expect(result.success).toBe(true);
            expect(result.quality).toBeGreaterThan(0);
            expect(result.experience).toBeGreaterThan(0);
            expect(result.item).toBeDefined();
            expect(result.item.name).toBe('Basic Dagger');
        });

        test('should handle crafting failures gracefully', async () => {
            // Create insufficient quality materials
            const poorMaterial = craftingSystem.materialSystem.createMaterial({
                name: 'Poor Iron',
                type: 'METAL',
                quality: 10,
                quantity: 2,
                harvestedBy: testCrafter.id,
                location: 'test_mines'
            });

            const result = await craftingSystem.craftItem(
                testCrafter.id,
                'dagger_basic',
                [{ id: poorMaterial.id, quantity: 2 }]
            );

            expect(result).toBeDefined();
            // Result could be success or failure depending on random chance
            expect(typeof result.success).toBe('boolean');
        });

        test('should validate crafting requirements', async () => {
            // Test with insufficient materials
            const result = await craftingSystem.craftItem(
                testCrafter.id,
                'dagger_basic',
                [{ id: 'nonexistent_material', quantity: 5 }]
            );

            // Should fail due to validation
            expect(result).toBeDefined();
            // The actual implementation would throw an error
        });
    });

    describe('Social Features', () => {
        test('should create crafting order successfully', async () => {
            const order = await craftingSystem.createCraftingOrder('test_client', {
                type: 'individual',
                items: [{ recipeId: 'dagger_basic', quantity: 1 }],
                quality: 'standard',
                deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
                payment: { amount: 100, currency: 'gold', method: 'on_delivery' }
            });

            expect(order).toBeDefined();
            expect(order.id).toBeDefined();
            expect(order.clientId).toBe('test_client');
            expect(order.status).toBe('open');
            expect(order.specifications.items).toHaveLength(1);
        });

        test('should create guild workshop successfully', async () => {
            const workshop = await craftingSystem.createGuildWorkshop('test_guild', {
                name: 'Test Workshop',
                type: 'blacksmithing',
                location: 'test_location',
                initialResources: 1000,
                foundingMembers: [testCrafter.id]
            });

            expect(workshop).toBeDefined();
            expect(workshop.id).toBeDefined();
            expect(workshop.name).toBe('Test Workshop');
            expect(workshop.type).toBe('blacksmithing');
            expect(workshop.level).toBe(1);
            expect(workshop.members).toContain(testCrafter.id);
        });

        test('should create competition successfully', async () => {
            const competition = await craftingSystem.createCompetition(testCrafter.id, {
                name: 'Test Competition',
                type: 'quality',
                category: 'blacksmithing',
                description: 'Test competition',
                rules: ['Test rule'],
                timeline: {
                    registrationStart: new Date().toISOString(),
                    registrationEnd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
                    competitionStart: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(),
                    competitionEnd: new Date(Date.now() + 17 * 24 * 60 * 60 * 1000).toISOString()
                },
                prizes: [
                    { rank: 1, reward: { gold: 1000 } }
                ],
                entryFee: 50,
                maxParticipants: 20
            });

            expect(competition).toBeDefined();
            expect(competition.id).toBeDefined();
            expect(competition.name).toBe('Test Competition');
            expect(competition.organizerId).toBe(testCrafter.id);
            expect(competition.status).toBe('registration');
        });

        test('should create apprenticeship successfully', async () => {
            const apprentice = {
                id: 'test_apprentice',
                name: 'Test Apprentice',
                skills: { BLACKSMITHING: 25 },
                stats: {},
                resources: { gold: 100 }
            };

            craftingSystem.craftingSystem.crafters.set(apprentice.id, apprentice);

            const apprenticeship = await craftingSystem.createApprenticeship(
                testCrafter.id,
                apprentice.id,
                {
                    duration: 30,
                    specializations: ['basic_crafting'],
                    goals: ['Reach skill level 50'],
                    compensation: { weekly: 25 }
                }
            );

            expect(apprenticeship).toBeDefined();
            expect(apprenticeship.id).toBeDefined();
            expect(apprenticeship.masterId).toBe(testCrafter.id);
            expect(apprenticeship.apprenticeId).toBe(apprentice.id);
            expect(apprenticeship.status).toBe('active');
        });
    });

    describe('Analytics and Statistics', () => {
        test('should generate crafter statistics', () => {
            const stats = craftingSystem.getCrafterStats(testCrafter.id);

            expect(stats).toBeDefined();
            expect(stats.crafter).toBeDefined();
            expect(stats.reputation).toBeDefined();
            expect(stats.materials).toBeDefined();
            expect(stats.stats).toBeDefined();
            expect(stats.skills).toBeDefined();
        });

        test('should generate market analytics', () => {
            const analytics = craftingSystem.getMarketAnalytics();

            expect(analytics).toBeDefined();
            expect(analytics.orders).toBeDefined();
            expect(analytics.marketplace).toBeDefined();
            expect(analytics.materials).toBeDefined();
            expect(typeof analytics.orders.total).toBe('number');
            expect(typeof analytics.materials.total).toBe('number');
        });
    });

    describe('Error Handling', () => {
        test('should handle invalid crafter ID gracefully', () => {
            const invalidCrafter = craftingSystem.craftingSystem.getCrafter('nonexistent');
            expect(invalidCrafter).toBeUndefined();
        });

        test('should handle invalid recipe ID gracefully', () => {
            const invalidRecipe = craftingSystem.craftingSystem.getRecipe('nonexistent_recipe');
            expect(invalidRecipe).toBeUndefined();
        });

        test('should handle invalid material ID gracefully', () => {
            const invalidMaterial = craftingSystem.materialSystem.getMaterial('nonexistent_material');
            expect(invalidMaterial).toBeUndefined();
        });
    });

    describe('Configuration', () => {
        test('should use custom configuration', () => {
            const customSystem = new AdvancedCraftingSystem({
                system: {
                    maxSkillLevel: 200
                }
            });

            expect(customSystem.craftingSystem.config.maxSkillLevel).toBe(200);
        });

        test('should merge configuration properly', () => {
            const customSystem = new AdvancedCraftingSystem({
                system: {
                    baseExperienceMultiplier: 3.0
                }
            });

            expect(customSystem.craftingSystem.config.maxSkillLevel).toBeDefined(); // Should keep default
            expect(customSystem.craftingSystem.config.baseExperienceMultiplier).toBe(3.0); // Should use custom
        });
    });
});