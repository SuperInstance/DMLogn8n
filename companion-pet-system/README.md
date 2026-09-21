# DMlogn8n Companion Pet System

A comprehensive AI-driven pet companion system for D&D campaigns and RPG games, featuring advanced pet AI, evolution mechanics, combat systems, and complete n8n workflow automation.

## 🌟 Features

### 🐾 Pet Types & Acquisition
- **50+ Pet Types**: Animals, magical creatures, undead, constructs, and more
- **Multiple Acquisition Methods**: Taming, summoning, breeding, quest rewards, and seasonal events
- **Rarity Tiers**: Common, Uncommon, Rare, Epic, and Legendary
- **Special Event Pets**: Seasonal and limited-time companions
- **Custom Pet Creation**: Create unique pets with magical abilities

### 🧠 Advanced AI Behavior
- **Personality-Driven Actions**: 15+ personality traits affecting behavior
- **Learning System**: Pets learn from player actions and environment
- **Emotional States**: Complex mood system with 11 emotional states
- **Autonomous Decision Making**: Pets make independent decisions based on needs and personality
- **Social Interactions**: Pets interact with each other and form relationships

### ⚡ Evolution System
- **5 Evolution Stages**: Visual transformations with stat increases
- **Skill Tree Customization**: Branching skill paths for each pet type
- **Ability Unlocking**: Progressive ability acquisition
- **Genetic Traits**: Inherited and mutated traits from breeding
- **Special Evolution Conditions**: Unique requirements for rare evolutions

### ⚔️ Combat & Utility
- **Pet Combat System**: Turn-based combat with unique abilities
- **Support & Healing**: Healing, buffing, and protective abilities
- **Utility Skills**: Tracking, scouting, crafting, and exploration
- **Mount Capabilities**: Large pets can serve as mounts
- **Tournament System**: Organized pet battles with rankings and rewards

### 🏡 Pet Care & Bonding
- **Feeding System**: Dietary preferences and nutritional needs
- **Grooming & Hygiene**: Cleanliness management and cosmetic care
- **Training & Development**: Skill training and behavior modification
- **Housing System**: Customizable habitats with decorations and upgrades
- **Bonding Activities**: Interactive activities to strengthen relationships

## 🚀 Quick Start

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-repo/DMlogn8n-companion-pet-system.git
cd DMlogn8n-companion-pet-system
```

2. Install dependencies:
```bash
npm install
```

3. Set up the configuration:
```bash
cp config/pet-system-config.json.example config/pet-system-config.json
# Edit the configuration file with your settings
```

4. Start the system:
```bash
npm start
```

### Basic Usage

```javascript
// Import the core components
const PetDatabase = require('./src/core/PetDatabase');
const Pet = require('./src/core/Pet');
const PetAcquisition = require('./src/core/PetAcquisition');
const PetAI = require('./src/ai/PetAI');
const PetCare = require('./src/care/PetCare');
const EvolutionSystem = require('./src/evolution/EvolutionSystem');
const PetCombat = require('./src/combat/PetCombat');

// Initialize the system
const petDatabase = new PetDatabase();
const petAcquisition = new PetAcquisition(petDatabase, playerManager);
const evolutionSystem = new EvolutionSystem(petDatabase);

// Create a new pet
const wolfType = petDatabase.getPetType('wolf');
const pet = new Pet(wolfType, 'player123', 'Shadow');

// Initialize AI
const petAI = new PetAI(pet, world);

// Care for your pet
const petCare = new PetCare(petDatabase, world);
await petCare.performCareAction(pet, 'feed', { food: 'meat', amount: 'large' });

// Train your pet
await petCare.performCareAction(pet, 'train', { skill: 'sit', method: 'positive_reinforcement' });

// Check evolution readiness
const evolutionReadiness = evolutionSystem.checkEvolutionReadiness(pet);
if (evolutionReadiness.ready) {
  await evolutionSystem.performEvolution(pet);
}
```

## 📚 System Architecture

### Core Components

- **`src/core/`**: Core pet management classes
  - `PetDatabase.js`: Database of all pet types and their properties
  - `Pet.js`: Main pet class with stats, behaviors, and status
  - `PetAcquisition.js`: Pet acquisition methods (taming, summoning, breeding)

- **`src/ai/`**: AI behavior and emotional systems
  - `PetAI.js`: Main AI controller with decision-making logic
  - `EmotionalSystem.js`: Complex emotional state management

- **`src/evolution/`**: Evolution and skill progression
  - `EvolutionSystem.js`: 5-stage evolution with skill trees
  - Evolution requirements and special conditions

- **`src/combat/`**: Combat and utility mechanics
  - `PetCombat.js`: Turn-based combat system with abilities
  - Tournament management and battle mechanics

- **`src/care/`**: Pet care and housing
  - `PetCare.js`: Comprehensive care system
  - `PetTrainingSystem.js`: Skill training and behavior modification
  - `PetHousingSystem.js`: Habitat management and customization

- **`src/workflows/`**: n8n automation workflows
  - `pet-care-routine.json`: Automated pet care scheduling
  - `evolution-processing.json`: Evolution opportunity checking
  - `training-automation.json`: Training session automation

## 🎮 Pet Types

### Common Pets
- **Wolf**: L pack hunters with alpha potential
- **Cat**: Independent and curious companions
- **Owl**: Wise nocturnal hunters with enhanced perception

### Uncommon Pets
- **Fairy Dragon**: Playful magical creatures with pixie abilities
- **Shadow Wolf**: Stealthy predators with dark affinity
- **Clockwork Familiar**: Mechanical assistants with precision skills

### Rare Pets
- **Phoenix**: Immortal birds with rebirth abilities
- **Ice Elemental**: Cold-immune beings with frost powers
- **Griffin**: Majestic aerial hunters with noble presence

### Epic Pets
- **Dragon Whelp**: Young dragons with growing power
- **Skeletal Hound**: Undead hunters with bone-shattering attacks
- **Unicorn**: Pure healers with purifying abilities

### Legendary Pets
- **Ancient Dragon**: Powerful wyrms with ancient wisdom
- **Celestial Guardian**: Divine protectors with holy powers
- **Void Stalker**: Reality-bending entities from the void

## 🧬 Pet Personalities

Each pet has a unique personality combination that affects their behavior:

- **Playful**: Energetic and fun-loving, enjoys play activities
- **Serious**: Focused and disciplined, excels at training
- **Curious**: Inquisitive and adventurous, loves exploration
- **Timid**: Cautious and shy, needs gentle handling
- **Brave**: Courageous and protective, natural guardians
- **Affectionate**: Loving and social, bonds strongly with owners
- **Independent**: Self-reliant and autonomous, prefers freedom
- **Protective**: Loyal and watchful, excellent guardians
- **Gentle**: Calm and kind, good with other creatures
- **Mischievous**: Playful troublemakers with clever tricks
- **Loyal**: Devoted and faithful, deeply bonded
- **Adventurous**: Bold explorers who love new experiences

## ⚔️ Combat Abilities

### Attack Abilities
- **Bite**: Basic physical attack
- **Claw**: Sharp claw attack with critical chance
- **Fire Breath**: Elemental fire damage with burn effect
- **Ice Shard**: Cold damage with freezing chance
- **Shadow Blend**: Stealth attack from shadows

### Support Abilities
- **Healing Aura**: Area-of-effect healing
- **Protective Barrier**: Damage absorption shield
- **Battle Roar**: Buffs allies with attack boost
- **Rebirth Flame**: Revive fallen allies

### Ultimate Abilities
- **Cataclysm Breath**: Massive dragon breath attack
- **Summon Spirit Pack**: Call ancestral wolf spirits
- **Solar Resurrection**: Full party revival with buffs

## 🏠 Housing System

### Habitat Types
- **Basic Den**: Simple starter habitat
- **Enchanted Forest**: Magical environment for magical pets
- **Volcanic Lair**: Fire-themed habitat for fire creatures
- **Arctic Cave**: Cold environment for ice pets
- **Celestial Sanctuary**: Divine space for holy creatures

### Customization Options
- **Decorations**: Furniture, toys, and environmental items
- **Amenities**: Training equipment, grooming stations
- **Upgrades**: Space expansion, comfort improvements
- **Themes**: Seasonal and special event decorations

## 🔄 n8n Workflows

### Pet Care Routine
- **Frequency**: Hourly checks
- **Actions**: Automatic feeding, grooming, play, rest
- **Priority System**: Urgent needs addressed first
- **Logging**: Comprehensive care history tracking

### Evolution Processing
- **Frequency**: Every 30 minutes
- **Eligibility Check**: Automatic evolution readiness detection
- **Special Evolutions**: Check for rare evolution conditions
- **Notifications**: Evolution completion alerts

### Training Automation
- **Frequency**: Every 6 hours
- **Skill Assessment**: Identify training opportunities
- **Method Selection**: Optimal training methods per pet
- **Progress Tracking**: Skill development analytics

## 🎯 Integration with DMlogn8n

### Inventory Management
- Pet equipment and items stored in player inventory
- Seamless transfer between pet and player items
- Special pet-specific equipment slots

### Combat System Integration
- Pets participate in D&D combat encounters
- Pet actions use standard action economy
- Experience and leveling synchronized with player progression

### Player Housing
- Pet habitats integrated into player housing
- Shared space usage and customization
- Multi-pet household management

## 📊 Data Management

### Pet Persistence
```javascript
// Save pet data
const petData = pet.toJSON();
await savePetToDatabase(pet.id, petData);

// Load pet data
const loadedPetData = await loadPetFromDatabase(petId);
const loadedPet = Pet.fromJSON(loadedPetData);
```

### Analytics and Reporting
- Care history and trends
- Training progress and skill development
- Combat performance statistics
- Evolution milestones and achievements

## 🔧 Configuration

### System Configuration (`config/pet-system-config.json`)
```json
{
  "gameplay": {
    "maxActivePets": 5,
    "maxPetLevel": 100,
    "evolutionStages": 5,
    "trainingCooldownMinutes": 60
  },
  "ai": {
    "updateInterval": 5000,
    "learningRate": 0.01,
    "autonomousActions": true
  },
  "evolution": {
    "experienceMultiplier": 1.0,
    "skillPointRate": 1
  }
}
```

### Pet Type Configuration
Each pet type includes:
- Base stats and abilities
- Preferred habitat and diet
- Personality tendencies
- Acquisition methods
- Evolution paths

## 🧪 Testing

### Unit Tests
```bash
npm test
```

### Integration Tests
```bash
npm run test:integration
```

### End-to-End Tests
```bash
npm run test:e2e
```

## 🚀 Deployment

### Production Setup
1. Set environment variables
2. Configure database connections
3. Set up n8n workflows
4. Initialize pet database
5. Start monitoring systems

### Environment Variables
```bash
NODE_ENV=production
DATABASE_URL=your_database_url
N8N_WEBHOOK_URL=your_n8n_webhook_url
LOG_LEVEL=info
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### Development Guidelines
- Follow ESLint configuration
- Write comprehensive tests
- Update documentation
- Use semantic versioning

## 📝 Changelog

### Version 1.0.0
- Initial release
- Core pet system implementation
- AI behavior system
- Evolution mechanics
- Combat system
- Care and housing
- n8n workflow integration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Check the `/docs` directory for detailed guides
- **Community**: Join our Discord server for discussions
- **Email**: support@dmlogn8n-pets.com

## 🙏 Acknowledgments

- DMlogn8n community for feedback and suggestions
- n8n team for excellent workflow automation
- D&D community for inspiration and mechanics
- Open source contributors and testers

---

**DMlogn8n Companion Pet System** - Bringing your adventures to life with intelligent, evolving companions! 🐾✨