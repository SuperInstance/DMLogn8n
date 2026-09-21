/**
 * Quick Start Example for Advanced Crafting System
 * Demonstrates basic usage of the crafting system
 */

const AdvancedCraftingSystem = require('../index.js');

async function quickStartExample() {
    console.log('🔨 Advanced Crafting System - Quick Start Example\n');

    // Initialize the crafting system
    const craftingSystem = new AdvancedCraftingSystem({
        system: {
            maxSkillLevel: 500,
            baseExperienceMultiplier: 2.0 // Faster progression for demo
        },
        debugging: {
            enabled: true,
            logLevel: 'info'
        }
    });

    // Create a test crafter
    const crafter = {
        id: 'example_crafter_001',
        name: 'Thorin Ironforge',
        skills: {
            BLACKSMITHING: 150,
            ALCHEMY: 50
        },
        stats: {
            totalCrafts: 0,
            successfulCrafts: 0,
            criticalSuccesses: 0
        },
        resources: {
            gold: 2000
        },
        unlockedRecipes: [],
        achievements: []
    };

    // Register the crafter
    craftingSystem.craftingSystem.crafters.set(crafter.id, crafter);
    console.log(`✅ Created crafter: ${crafter.name} (Blacksmithing: ${crafter.skills.BLACKSMITHING})`);

    // Create some test materials
    const materials = [
        craftingSystem.materialSystem.createMaterial({
            name: 'Iron Ingot',
            type: 'METAL',
            quality: 75,
            quantity: 10,
            harvestedBy: crafter.id,
            location: 'iron_mines'
        }),
        craftingSystem.materialSystem.createMaterial({
            name: 'Steel Ingot',
            type: 'METAL',
            quality: 85,
            quantity: 5,
            harvestedBy: crafter.id,
            location: 'iron_mines'
        }),
        craftingSystem.materialSystem.createMaterial({
            name: 'Leather Strip',
            type: 'LEATHER',
            quality: 60,
            quantity: 8,
            harvestedBy: crafter.id,
            location: 'hunting_grounds'
        }),
        craftingSystem.materialSystem.createMaterial({
            name: 'Healing Herb',
            type: 'HERB',
            quality: 70,
            quantity: 15,
            harvestedBy: crafter.id,
            location: 'forest'
        })
    ];

    console.log(`✅ Created ${materials.length} materials for crafting`);

    try {
        // Example 1: Basic Crafting
        console.log('\n📦 Example 1: Basic Item Crafting');
        console.log('------------------------------------');

        const basicResult = await craftingSystem.craftItem(
            crafter.id,
            'dagger_basic',
            [
                { id: materials[0].id, quantity: 2 },
                { id: materials[2].id, quantity: 1 }
            ]
        );

        console.log(`🔨 Crafting Result: ${basicResult.success ? '✅ SUCCESS' : '❌ FAILED'}`);
        if (basicResult.success) {
            console.log(`📊 Item Quality: ${basicResult.quality}/100`);
            console.log(`💎 Experience Gained: ${basicResult.experience}`);
            console.log(`⚔️ Item Created: ${basicResult.item.name}`);
            console.log(`🛡️ Durability: ${basicResult.item.durability}`);
        }

        // Example 2: Advanced Crafting with Techniques
        console.log('\n⚡ Example 2: Advanced Crafting with Techniques');
        console.log('-----------------------------------------------');

        const advancedResult = await craftingSystem.craftWithTechnique(
            crafter.id,
            'blacksmithing',
            'longsword_steel',
            [
                { id: materials[1].id, quantity: 3 },
                { id: materials[2].id, quantity: 2 }
            ],
            ['FOLDING'],
            { qualityTarget: 85 }
        );

        console.log(`🔨 Advanced Crafting: ${advancedResult.success ? '✅ SUCCESS' : '❌ FAILED'}`);
        if (advancedResult.success) {
            console.log(`📊 Item Quality: ${advancedResult.quality}/100`);
            console.log(`💎 Experience Gained: ${advancedResult.experience}`);
            console.log(`⚔️ Item Created: ${advancedResult.item.name}`);
            console.log(`✨ Special Effects: ${advancedResult.item.properties.specialEffects?.join(', ') || 'None'}`);
        }

        // Example 3: Material Harvesting
        console.log('\n⛏️ Example 3: Material Harvesting');
        console.log('--------------------------------');

        const harvestResult = await craftingSystem.harvestMaterial(
            crafter.id,
            'mountains',
            'METAL',
            'iron_pickaxe',
            80
        );

        console.log(`⛏️ Harvesting Result: ${harvestResult.success ? '✅ SUCCESS' : '❌ FAILED'}`);
        if (harvestResult.success) {
            console.log(`📦 Materials Harvested: ${harvestResult.materials.length}`);
            harvestResult.materials.forEach((material, index) => {
                console.log(`  ${index + 1}. ${material.name} (Quality: ${material.quality})`);
            });
            console.log(`💎 Experience Gained: ${harvestResult.experience}`);
        }

        // Example 4: Custom Potion Brewing
        console.log('\n🧪 Example 4: Custom Potion Brewing');
        console.log('-----------------------------------');

        const potionResult = await craftingSystem.brewCustomPotion(
            crafter.id,
            'ELEMENTAL_SYNERGY',
            [
                { id: materials[3].id, quantity: 3 },
                { id: materials[3].id, quantity: 2 }
            ],
            { enhancePower: true }
        );

        console.log(`🧪 Potion Brewing: ${potionResult.success ? '✅ SUCCESS' : '❌ FAILED'}`);
        if (potionResult.success) {
            console.log(`🧪 Potion: ${potionResult.potion.name}`);
            console.log(`📊 Quality: ${potionResult.potion.quality}/100`);
            console.log(`⏱️ Duration: ${potionResult.potion.duration} seconds`);
            console.log(`🎯 Effects: ${potionResult.potion.effects.join(', ')}`);
        }

        // Example 5: Crafting Order System
        console.log('\n💼 Example 5: Crafting Order System');
        console.log('-----------------------------------');

        const order = await craftingSystem.createCraftingOrder('client_001', {
            type: 'individual',
            items: [{ recipeId: 'plate_armor_steel', quantity: 1 }],
            quality: 'masterwork',
            deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
            payment: { amount: 800, currency: 'gold', method: 'on_delivery' }
        });

        console.log(`📋 Order Created: ${order.id}`);
        console.log(`👤 Client: ${order.clientId}`);
        console.log(`💰 Payment: ${order.payment.amount} ${order.payment.currency}`);
        console.log(`⏰ Deadline: ${new Date(order.timeline.deadline).toLocaleDateString()}`);

        // Apply for the order
        const application = await craftingSystem.socialFeatures.applyForOrder(
            crafter.id,
            order.id,
            {
                estimatedTime: 7200, // 2 hours
                qualityGuarantee: 85,
                totalCost: 750,
                approach: 'Traditional blacksmithing with pattern welding technique'
            }
        );

        console.log(`📝 Application Submitted: ${application.id}`);
        console.log(`💰 Proposed Cost: ${application.proposal.totalCost} gold`);
        console.log(`🎯 Quality Guarantee: ${application.proposal.qualityGuarantee}%`);

        // Example 6: Guild Workshop Creation
        console.log('\n🏰 Example 6: Guild Workshop Creation');
        console.log('------------------------------------');

        const workshop = await craftingSystem.createGuildWorkshop('guild_001', {
            name: 'Ironforge Forge',
            type: 'blacksmithing',
            location: 'ironforge_mountain',
            initialResources: 5000,
            foundingMembers: [crafter.id]
        });

        console.log(`🏰 Workshop Created: ${workshop.name}`);
        console.log(`🔧 Type: ${workshop.type}`);
        console.log(`📍 Location: ${workshop.location}`);
        console.log(`💰 Resources: ${workshop.resources}`);
        console.log(`✨ Bonuses: ${JSON.stringify(workshop.bonuses)}`);

        // Example 7: Competition Creation
        console.log('\n🏆 Example 7: Crafting Competition');
        console.log('---------------------------------');

        const competition = await craftingSystem.createCompetition('guild_master_001', {
            name: 'Annual Masters\' Competition',
            type: 'quality',
            category: 'blacksmithing',
            description: 'Showcase your finest blacksmithing work',
            rules: [
                'All work must be original',
                'No magical enhancements above rank 3',
                'Submit by the deadline for judging'
            ],
            timeline: {
                registrationStart: new Date().toISOString(),
                registrationEnd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
                competitionStart: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000).toISOString(),
                competitionEnd: new Date(Date.now() + 17 * 24 * 60 * 60 * 1000).toISOString()
            },
            prizes: [
                { rank: 1, reward: { gold: 5000, title: 'Master Blacksmith' } },
                { rank: 2, reward: { gold: 2500, rare_materials: 10 } },
                { rank: 3, reward: { gold: 1000, crafting_tools: 'masterwork' } }
            ],
            entryFee: 100,
            maxParticipants: 50
        });

        console.log(`🏆 Competition Created: ${competition.name}`);
        console.log(`📅 Registration: ${new Date(competition.timeline.registrationStart).toLocaleDateString()} - ${new Date(competition.timeline.registrationEnd).toLocaleDateString()}`);
        console.log(`💰 Entry Fee: ${competition.entryFee} gold`);
        console.log(`🎯 Max Participants: ${competition.maxParticipants}`);

        // Example 8: Master-Apprentice Relationship
        console.log('\n👨‍🏫 Example 8: Master-Apprentice System');
        console.log('--------------------------------------');

        const apprentice = {
            id: 'apprentice_001',
            name: 'Fili Stonehand',
            skills: {
                BLACKSMITHING: 25
            },
            stats: {},
            resources: { gold: 100 }
        };

        craftingSystem.craftingSystem.crafters.set(apprentice.id, apprentice);

        const apprenticeship = await craftingSystem.createApprenticeship(
            crafter.id,
            apprentice.id,
            {
                duration: 90, // 90 days
                specializations: ['weapon_crafting', 'armor_crafting'],
                goals: [
                    'Reach skill level 100',
                    'Craft 50 items',
                    'Achieve 70% average quality'
                ],
                compensation: {
                    weekly: 50,
                    bonus_on_completion: 200
                }
            }
        );

        console.log(`👨‍🏫 Apprenticeship Created`);
        console.log(`🎓 Master: ${crafter.name}`);
        console.log(`👶 Apprentice: ${apprentice.name}`);
        console.log(`⏰ Duration: ${apprenticeship.terms.duration} days`);
        console.log(`🎯 Specializations: ${apprenticeship.terms.specializations.join(', ')}`);

        // Example 9: Market Analytics
        console.log('\n📊 Example 9: System Analytics');
        console.log('----------------------------');

        const analytics = craftingSystem.getMarketAnalytics();
        console.log(`📦 Active Orders: ${analytics.orders.active}`);
        console.log(`💰 Average Order Value: ${analytics.orders.averageValue} gold`);
        console.log(`🏪 Marketplace Listings: ${analytics.marketplace.activeListings}`);
        console.log(`📊 Total Materials: ${analytics.materials.total}`);
        console.log(`⭐ Average Material Quality: ${analytics.materials.averageQuality.toFixed(1)}`);

        // Example 10: Crafter Statistics
        console.log('\n👤 Example 10: Crafter Statistics');
        console.log('--------------------------------');

        const crafterStats = craftingSystem.getCrafterStats(crafter.id);
        console.log(`🔨 Total Crafts: ${crafterStats.stats.totalCrafts || 0}`);
        console.log(`✅ Successful Crafts: ${crafterStats.stats.successfulCrafts || 0}`);
        console.log(`💎 Critical Successes: ${crafterStats.stats.criticalSuccesses || 0}`);
        console.log(`📦 Materials: ${crafterStats.materials.count}`);
        console.log(`💰 Material Value: ${crafterStats.materials.totalValue} gold`);
        console.log(`⭐ Reputation: ${crafterStats.reputation.overall.toFixed(1)}/5.0`);

        console.log('\n🎉 Quick Start Example Completed Successfully!');
        console.log('💡 Explore more features in the documentation: /docs/');

    } catch (error) {
        console.error('❌ Error during example execution:', error.message);
        console.error(error.stack);
    }
}

// Run the example if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    quickStartExample();
}

export default quickStartExample;