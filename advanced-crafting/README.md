# Advanced Crafting System for DMlogn8n

A comprehensive, multi-tier crafting system designed for D&D and roleplaying game campaigns, featuring complex item creation mechanics, social features, and full n8n workflow automation.

## 🎯 Features

### Multi-Tier Crafting System
- **Simple Crafting**: Basic items with common materials and straightforward recipes
- **Advanced Crafting**: Complex items requiring rare materials and specialized skills
- **Master Crafting**: Legendary items created with master techniques and rare components
- **Artifact Creation**: Unique artifacts requiring quest completion and legendary components
- **Magical Infusion**: Enchanting and magical imbuing with arcane energies

### Crafting Professions
- **Blacksmithing**: Weapons, armor, and tools with advanced metallurgy
- **Alchemy**: Potions, elixirs, and magical substances with custom formulas
- **Enchanting**: Magical enhancements and rune creation
- **Tailoring**: Clothing, robes, bags, and textile items
- **Jewelcrafting**: Rings, amulets, and gem cutting
- **Woodworking**: Bows, staves, furniture, and wooden crafts
- **Cooking**: Food and buff items with various effects
- **Inscription**: Scrolls, tomes, and written magical items

### Material System
- **Quality Tiers**: Common, Uncommon, Rare, Epic, and Legendary materials
- **Harvesting Mechanics**: Location-based gathering with environmental factors
- **Material Properties**: Complex attribute system affecting final item quality
- **Decay System**: Material deterioration requiring proper storage
- **Market Integration**: Trading and marketplace functionality

### Advanced Mechanics
- **Skill Progression**: Experience-based leveling with mastery tiers
- **Critical Success/Failure**: Dynamic outcomes with special effects
- **Pattern Discovery**: Recipe experimentation and learning system
- **Quality Rating**: Comprehensive item quality calculation
- **Tool Requirements**: Equipment affecting crafting success and quality

### Social Features
- **Crafting Orders**: Commission system with client-crafter relationships
- **Guild Workshops**: Shared crafting spaces with bonuses and management
- **Competitions**: Crafting contests with prizes and recognition
- **Master-Apprentice**: Learning system with progression tracking
- **Reputation System**: Community feedback and reliability scoring

## 🏗️ Architecture

```
advanced-crafting/
├── core/                    # Core system components
│   ├── CraftingSystem.js    # Main crafting engine
│   └── SocialFeatures.js    # Social interactions system
├── professions/             # Crafting profession modules
│   ├── blacksmithing/       # Blacksmithing profession
│   ├── alchemy/            # Alchemy profession
│   └── [other professions] # Additional crafting professions
├── materials/              # Material management system
│   └── MaterialSystem.js   # Material properties and harvesting
├── workflows/              # n8n automation workflows
│   └── n8n/                # n8n workflow definitions
├── config/                 # Configuration files
│   └── crafting-config.js  # System configuration
├── api/                    # API endpoints
├── tests/                  # Test suites
└── docs/                   # Documentation
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd DMlogn8n/advanced-crafting

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Basic Usage

```javascript
// Initialize the crafting system
const AdvancedCraftingSystem = require('./index');
const craftingSystem = new AdvancedCraftingSystem();

// Create a new crafter
const crafter = {
    id: 'player_001',
    name: 'Gandalf',
    skills: {
        BLACKSMITHING: 150,
        ALCHEMY: 200
    },
    stats: {},
    resources: {
        gold: 1000
    }
};

craftingSystem.craftingSystem.crafters.set(crafter.id, crafter);

// Craft an item
const result = await craftingSystem.craftItem(
    'player_001',
    'longsword_steel',
    [
        { id: 'steel_ingot', quantity: 3 },
        { id: 'leather_strip', quantity: 2 }
    ],
    { useTechniques: ['FOLDING'] }
);

console.log(result);
```

### Material Harvesting

```javascript
// Harvest materials
const harvestResult = await craftingSystem.harvestMaterial(
    'player_001',
    'iron_mines',
    'METAL',
    'iron_pickaxe',
    75
);

console.log(`Harvested ${harvestResult.materials.length} materials`);
```

### Social Features

```javascript
// Create a crafting order
const order = await craftingSystem.createCraftingOrder('client_001', {
    type: 'individual',
    items: [{ recipeId: 'plate_armor_steel', quantity: 1 }],
    quality: 'masterwork',
    deadline: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    payment: { amount: 500, currency: 'gold', method: 'on_delivery' }
});

// Apply for the order
const application = await craftingSystem.socialFeatures.applyForOrder(
    'player_001',
    order.id,
    {
        estimatedTime: 3600,
        qualityGuarantee: 85,
        totalCost: 450,
        approach: 'Traditional blacksmithing with pattern welding'
    }
);
```

## ⚙️ Configuration

The system is highly configurable through the `crafting-config.js` file:

```javascript
const CraftingConfig = {
    system: {
        maxSkillLevel: 1000,
        baseExperienceMultiplier: 1.0,
        qualityDecayEnabled: true
    },
    tiers: {
        SIMPLE: {
            requiredSkill: 0,
            successBonus: 0.2,
            qualityMultiplier: 1.0
        },
        // ... other tiers
    },
    professions: {
        BLACKSMITHING: {
            primaryStats: ['strength', 'dexterity', 'intelligence'],
            tools: ['hammer', 'tongs', 'anvil', 'forge']
        }
        // ... other professions
    }
};
```

## 🔧 n8n Integration

The system includes comprehensive n8n workflows for automation:

### Crafting Automation Workflow
- **Webhook Trigger**: Receives crafting requests
- **Validation**: Checks requirements and materials
- **Processing**: Handles individual and mass production
- **Progress Tracking**: Real-time status updates
- **Quality Control**: Automated quality assurance
- **Inventory Integration**: Automatic item addition

### Guild Workshop Management
- **Workshop Creation**: Setup and configuration
- **Access Control**: Member permissions and roles
- **Resource Management**: Shared resources and upgrades
- **Activity Tracking**: Workshop usage statistics

### Competition Management
- **Event Organization**: Setup and registration
- **Submission Processing**: Entry handling and judging
- **Results Calculation**: Automated scoring and ranking
- **Prize Distribution**: Reward management

## 📊 API Reference

### Core Crafting Methods

#### `craftItem(crafterId, recipeId, materials, options)`
Craft an item with specified materials and options.

**Parameters:**
- `crafterId` (string): ID of the crafter
- `recipeId` (string): ID of the recipe to craft
- `materials` (array): Array of material objects with id and quantity
- `options` (object): Optional crafting parameters

**Returns:** Crafting result object with success status, item details, and experience gained

#### `harvestMaterial(harvesterId, location, materialType, toolId, skill)`
Harvest materials from a specified location.

**Parameters:**
- `harvesterId` (string): ID of the harvester
- `location` (string): Harvesting location/zone
- `materialType` (string): Type of material to harvest
- `toolId` (string): ID of harvesting tool
- `skill` (number): Harvesting skill level

**Returns:** Harvest result with materials and experience

### Social Feature Methods

#### `createCraftingOrder(clientId, orderDetails)`
Create a new crafting order for other players to fulfill.

**Parameters:**
- `clientId` (string): ID of the client placing the order
- `orderDetails` (object): Order specifications, items, payment, and timeline

**Returns:** Order object with ID and status

#### `createGuildWorkshop(guildId, workshopDetails)`
Create a shared guild workshop for collaborative crafting.

**Parameters:**
- `guildId` (string): ID of the guild
- `workshopDetails` (object): Workshop configuration and founding members

**Returns:** Workshop object with bonuses and settings

## 🎮 Game Integration

### D&D 5e Integration

The system is designed to integrate seamlessly with D&D 5e:

```javascript
// D&D character skills mapping
const dndSkills = {
    BLACKSMITHING: 'Tinker\'s Tools',
    ALCHEMY: 'Alchemist\'s Supplies',
    TAILORING: 'Weaver\'s Tools',
    WOODWORKING: 'Carpenter\'s Tools',
    JEWELCRAFTING: 'Jeweler\'s Tools',
    COOKING: 'Cooking Utensils'
};

// Convert D&D proficiency bonus to crafting bonus
function getCraftingBonus(proficient, expertise) {
    let bonus = 0;
    if (proficient) bonus += 2;
    if (expertise) bonus += 2;
    return bonus;
}
```

### Campaign Integration

```javascript
// Quest-based recipe unlocking
function unlockQuestRecipes(player, completedQuests) {
    const questRecipes = {
        'defeat_dragon': ['dragon_scale_armor', 'flame_sword'],
        'explore_dungeon': ['dungeon_looting_tools', 'darkvision_potion'],
        'save_kingdom': ['royal_crest_shield', 'noble_sword']
    };

    completedQuests.forEach(quest => {
        if (questRecipes[quest]) {
            questRecipes[quest].forEach(recipeId => {
                player.unlockedRecipes.push(recipeId);
            });
        }
    });
}
```

## 🔍 Advanced Features

### Custom Recipe Creation

```javascript
// Create a custom recipe
const customRecipe = {
    id: 'custom_moonblade',
    name: 'Moonblade of the Ancients',
    type: 'weapon',
    tier: 'MASTER',
    requiredSkill: 450,
    materials: [
        { id: 'moonsteel_ingot', quantity: 3 },
        { id: 'moonstone_crystal', quantity: 2 },
        { id: 'silver_essence', quantity: 1 },
        { id: 'enchanting_rune', quantity: 1 }
    ],
    baseProperties: {
        damage: 65,
        durability: 400,
        magicalDamage: 25,
        specialEffect: 'lunar_power'
    }
};

craftingSystem.craftingSystem.recipes.set(customRecipe.id, customRecipe);
```

### Dynamic Material Properties

```javascript
// Create materials with custom properties
const enchantedWood = craftingSystem.materialSystem.createMaterial({
    name: 'Enchanted Ironwood',
    type: 'WOOD',
    quality: 85,
    properties: {
        magical_resonance: 75,
        durability: 90,
        weight: 45
    },
    specialEffects: ['self_repairing', 'spell_resistance'],
    tags: ['magical', 'rare', 'woodworking']
});
```

### Competition Organization

```javascript
// Create a crafting competition
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
        registrationStart: new Date(),
        registrationEnd: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        competitionStart: new Date(Date.now() + 10 * 24 * 60 * 60 * 1000),
        competitionEnd: new Date(Date.now() + 17 * 24 * 60 * 60 * 1000)
    },
    prizes: [
        { rank: 1, reward: { gold: 5000, title: 'Master Blacksmith' } },
        { rank: 2, reward: { gold: 2500, rare_materials: 10 } },
        { rank: 3, reward: { gold: 1000, crafting_tools: 'masterwork' } }
    ],
    entryFee: 100,
    maxParticipants: 50
});
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
npm test

# Run specific test categories
npm run test:crafting
npm run test:social
npm run test:materials

# Run with coverage
npm run test:coverage
```

### Example Test

```javascript
const AdvancedCraftingSystem = require('../index');

describe('Crafting System', () => {
    let craftingSystem;
    let testCrafter;

    beforeEach(() => {
        craftingSystem = new AdvancedCraftingSystem();
        testCrafter = {
            id: 'test_crafter',
            skills: { BLACKSMITHING: 100 },
            stats: {},
            resources: { gold: 1000 }
        };
        craftingSystem.craftingSystem.crafters.set(testCrafter.id, testCrafter);
    });

    test('should craft basic item successfully', async () => {
        const result = await craftingSystem.craftItem(
            testCrafter.id,
            'dagger_basic',
            [{ id: 'iron_ingot', quantity: 2 }]
        );

        expect(result.success).toBe(true);
        expect(result.quality).toBeGreaterThan(0);
        expect(result.experience).toBeGreaterThan(0);
    });
});
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow the existing code style and patterns
- Add tests for new features
- Update documentation for API changes
- Ensure all tests pass before submitting

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- n8n team for the excellent workflow automation platform
- D&D community for inspiration and game mechanics
- Contributors and testers who helped shape this system

## 📞 Support

For support, feature requests, or bug reports:

- Create an issue on the GitHub repository
- Join our Discord community
- Check the documentation and FAQs

---

**Happy Crafting!** ⚒️✨