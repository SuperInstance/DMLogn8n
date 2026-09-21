# D&D 5e Rule Engine for DMlogn8n

A comprehensive, production-ready D&D 5th Edition rule engine that powers all gameplay mechanics in DMlogn8n. This system provides complete implementation of core D&D rules with validation, edge case handling, and performance optimization.

## Features

### 🎯 Core D&D Mechanics
- **Ability Checks** - Strength, Dexterity, Constitution, Intelligence, Wisdom, Charisma
- **Skill Checks** - All 18 official skills with proficiency and expertise support
- **Saving Throws** - Complete implementation with legendary resistance and special cases
- **Attack Rolls** - Melee and ranged attacks with advantage/disadvantage system
- **Damage Calculation** - Critical hits, resistance, immunity, vulnerability handling

### ⚔️ Combat System
- **Initiative Management** - Automatic rolling and turn order tracking
- **Turn-Based Combat** - Complete combat flow with action economy
- **Movement & Positioning** - Grid-based movement with speed management
- **Opportunity Attacks** - Reaction-based attacks with proper triggering
- **Special Actions** - Grapple, shove, trip, disarm, dodge, dash, ready actions
- **Cover System** - Half, three-quarters, and full cover mechanics

### 🧙 Spell System
- **Spell Slot Management** - Multi-class spellcasting with proper slot calculation
- **Concentration Mechanics** - Save DC calculation and concentration checks
- **Spell Effects** - Damage, healing, save-or-effect, attack roll, utility, summoning
- **Metamagic Support** - Framework for metamagic abilities
- **Ritual Casting** - Time-extended casting without spell slots
- **Higher Level Casting** - Automatic scaling for upcast spells

### 🦹 Condition System
- **All 15 Official Conditions** - Blinded, Charmed, Deafened, Exhaustion (6 levels), Frightened, Grappled, Incapacitated, Invisible, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious
- **Condition Interactions** - Automatic handling of conflicting conditions
- **Duration Tracking** - Round-based duration management
- **Condition Effects** - Comprehensive application of all mechanical effects

### 🎭 Character Features
- **Class Feature Automation** - Automatic application of class features by level
- **Racial Trait Processing** - Complete implementation of racial abilities
- **Feat Integration** - 20+ feats with proper prerequisites and effects
- **Multiclassing Support** - Proper multiclass rules and slot calculation
- **Level Advancement** - Automatic feature gaining and stat increases

## Installation

```bash
npm install
```

## Quick Start

```javascript
import DnD5eRuleEngine from './src/index.js';

// Create the rule engine
const engine = new DnD5eRuleEngine();

// Create a character
const fighter = engine.createCharacter({
  name: 'Aragorn',
  class: 'fighter',
  level: 5,
  abilities: { strength: 18, dexterity: 14, constitution: 16 }
});

// Perform ability check
const strengthCheck = engine.abilityCheck('fighter-id', 'strength', 15);
console.log(strengthCheck.success ? 'Success!' : 'Failure!');

// Start combat
const combat = engine.createCombat('battle-1');
engine.addCombatParticipant('battle-1', 'fighter-id', 18);
engine.startCombat('battle-1');

// Cast a spell
const spellResult = await engine.castSpell('wizard-id', 'fireball', {
  target: 'goblin-id',
  spellLevel: 3
});
```

## API Server

Start the REST API server:

```bash
npm start
```

The API will be available at `http://localhost:3000`

### API Endpoints

#### Characters
- `POST /api/characters` - Create character
- `GET /api/characters` - List characters
- `GET /api/characters/:id` - Get character
- `PUT /api/characters/:id` - Update character
- `DELETE /api/characters/:id` - Delete character

#### Dice & Rolls
- `POST /api/roll/dice` - Roll dice expression
- `POST /api/roll/d20` - Roll d20 with advantage/disadvantage
- `POST /api/rolls/ability-check` - Perform ability check
- `POST /api/rolls/skill-check` - Perform skill check
- `POST /api/rolls/saving-throw` - Perform saving throw

#### Combat
- `POST /api/combat/create` - Create combat encounter
- `POST /api/combat/:id/start` - Start combat
- `GET /api/combat/:id/state` - Get combat state
- `POST /api/combat/:id/attack` - Perform attack
- `POST /api/combat/:id/next-turn` - Next turn
- `POST /api/combat/:id/end` - End combat

#### Spells
- `POST /api/spells/cast` - Cast spell
- `GET /api/spells/search` - Search spells
- `GET /api/spells/by-level/:level` - Get spells by level

#### Conditions
- `POST /api/conditions/apply` - Apply condition
- `DELETE /api/conditions/:characterId/:condition` - Remove condition
- `GET /api/conditions/:characterId` - List character conditions

## Architecture

The rule engine is built with a modular architecture:

```
src/
├── core/           # Core mechanics and dice rolling
├── mechanics/      # Ability checks, skills, saving throws
├── combat/         # Combat management and actions
├── spells/         # Spell system and data
├── conditions/     # Condition management
├── features/       # Character features automation
├── types/          # Type definitions
├── api/            # REST API server
└── utils/          # Utility functions
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
npm test

# Run tests with coverage
npm run test:coverage

# Watch mode for development
npm run test:watch
```

The test suite includes:
- Unit tests for all core mechanics
- Integration tests for combat flows
- API endpoint testing
- Edge case validation
- Performance benchmarks

## Class Support

Currently supported classes with full feature automation:
- **Fighter** - Fighting styles, Action Surge, Extra Attack, Martial Archetypes
- **Rogue** - Expertise, Sneak Attack, Cunning Action, Roguish Archetypes
- **Wizard** - Arcane Recovery, Spellcasting, Arcane Traditions
- **Cleric** - Divine Domain, Channel Divinity, Spellcasting

## Spell Database

Includes 50+ spells across all levels with:
- Complete spell data (casting time, range, duration, components)
- Damage expressions with automatic scaling
- Save DC and attack bonus calculations
- Concentration and ritual support
- School of magic categorization

## Performance

- Optimized dice rolling with caching
- Efficient combat state management
- Minimal memory footprint
- Fast lookup tables for conditions and features
- Batch processing for multiple rolls

## Validation

Comprehensive rule validation including:
- Ability score bounds checking (1-20)
- Hit point and armor class validation
- Proficiency bonus verification
- Spell slot availability checking
- Condition conflict resolution
- Feat prerequisite validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Integration with DMlogn8n

This rule engine is designed to seamlessly integrate with DMlogn8n's existing infrastructure:

- Character AI integration for automated decision-making
- Voice chat interface for natural language commands
- Visual combat mapping and token management
- Real-time synchronization across clients
- Campaign and session persistence

The engine provides the mechanical foundation while DMlogn8n handles the presentation and user experience layers.