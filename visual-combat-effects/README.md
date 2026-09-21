# D&D Visual Combat Effects System

A stunning 3D visual combat effects system built with Three.js that brings D&D combat to life with beautiful animations, particle effects, and dynamic environments.

## ✨ Features

### 🎮 3D Combat Arena
- **WebGL/Three.js 3D Environment**: High-performance 3D rendering
- **Dynamic Lighting & Shadows**: Realistic lighting that changes with time of day
- **Particle Effects**: Beautiful spell and ability effects
- **Camera Controls**: Multiple camera angles including cinematic views
- **Grid-based Tactical Overlay**: Strategic combat grid

### 🏃 Character Animations
- **Smooth Animations**: Idle, walk, run, attack, casting, hurt, and death animations
- **Class-Specific Combat Moves**: Unique animations for each D&D class
- **Emotion & Expression**: Characters react to combat events
- **Spell Casting Gestures**: Realistic casting animations

### ✨ Spell Visual Effects
- **Fireball**: Explosive fire effects with particle trails
- **Lightning Chain**: Branching electrical effects
- **Healing**: Gentle light particle effects
- **Illusion**: Shimmering, ethereal visuals
- **Summoning**: Portal animations and mystical effects
- **Ice & Earth**: Elemental spell effects

### 📊 Combat Feedback
- **3D Damage Numbers**: Floating damage indicators
- **Critical Hit Effects**: Special visual feedback for criticals
- **Miss Indicators**: Visual cues for missed attacks
- **Status Effect Overlays**: Visual representations of buffs/debuffs
- **Animated Combat Log**: Real-time combat updates

### 🌍 Environmental Interactions
- **Destructible Objects**: Breakable barrels, crates, and more
- **Dynamic Weather**: Rain, snow, storms, and fog
- **Day/Night Cycle**: Realistic lighting transitions
- **Terrain Deformation**: Environmental damage effects
- **Interactive Elements**: Physics-based object interactions

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd visual-combat-effects

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Basic Usage

```typescript
import { CombatEffectsEngine, CharacterClass, SpellType } from './src/index.js'

// Initialize the engine
const canvas = document.getElementById('canvas')
const engine = new CombatEffectsEngine(canvas)

// Create characters
const warrior = {
  id: 'warrior_1',
  name: 'Aragorn',
  class: CharacterClass.Fighter,
  position: new THREE.Vector3(-5, 0, -5),
  health: 100,
  maxHealth: 100,
  level: 5,
  animationState: 'idle',
  statusEffects: []
}

engine.addCharacter(warrior)

// Cast spells
const fireballSpell = {
  id: 'fireball',
  name: 'Fireball',
  type: SpellType.Damage,
  damage: 30,
  radius: 5,
  speed: 0.8,
  color: 0xff6600,
  castTime: 1.5,
  particleEffect: {
    type: 'fire',
    count: 50,
    lifespan: 2,
    speed: 3,
    size: 0.3,
    colors: [0xff6600, 0xff9900, 0xffcc00]
  }
}

engine.castSpell('wizard_1', fireballSpell, targetPosition, 'warrior_1')

// Start the engine
engine.start()
```

## 🎯 Core Components

### CombatEffectsEngine
The main engine that coordinates all systems:
- Scene management and rendering
- Character lifecycle
- Spell casting coordination
- Performance optimization

### CharacterAnimator
Handles character animations:
- Smooth movement between positions
- Attack and casting animations
- State management (idle, walking, combat)
- Class-specific animation sets

### SpellEffectsManager
Manages all spell visual effects:
- Projectile creation and movement
- Impact effects and explosions
- Particle system coordination
- Spell type-specific behaviors

### CombatFeedbackSystem
Provides combat feedback:
- 3D damage numbers
- Status effect visuals
- Combat log management
- Miss and critical indicators

### EnvironmentalSystem
Manages environment interactions:
- Destructible objects
- Weather effects
- Day/night cycle
- Terrain modifications

## 🎨 Customization

### Creating Custom Spells

```typescript
const customSpell = {
  id: 'custom_spell',
  name: 'Custom Spell',
  type: SpellType.Damage,
  damage: 25,
  radius: 3,
  speed: 1.2,
  color: 0x00ff00,
  castTime: 1,
  particleEffect: {
    type: 'magic',
    count: 40,
    lifespan: 2.5,
    speed: 4,
    size: 0.25,
    colors: [0x00ff00, 0x00ff88, 0x88ff00],
    gravity: -2,
    spread: 1.5
  }
}
```

### Custom Character Classes

```typescript
// The system supports all standard D&D classes:
// - Fighter, Wizard, Rogue, Cleric, Barbarian, Ranger

// Each class has unique animations and visual effects
const character = {
  id: 'custom_character',
  name: 'Custom Hero',
  class: CharacterClass.Wizard,
  // ... other properties
}
```

### Environmental Setup

```typescript
// Custom environment configuration
const sceneConfig = {
  gridSize: 30,
  cellSize: 1,
  terrainType: 'dungeon',
  lighting: {
    ambientIntensity: 0.3,
    ambientColor: 0x404040,
    directionalIntensity: 0.6,
    directionalColor: 0x808080,
    shadows: true
  },
  timeOfDay: 20, // 8 PM
  weather: {
    type: WeatherType.Rain,
    intensity: 0.8
  }
}
```

## 🎮 Demo Controls

The interactive demo includes:

### Character Actions
- Move characters around the battlefield
- Perform attack animations
- Cast various spells
- Show miss indicators

### Spell Effects
- **Fireball**: Explosive fire damage
- **Ice Bolt**: Freezing projectile
- **Lightning**: Chain lightning effects
- **Healing**: Restorative magic
- **Buff**: Enhancement effects
- **Illusion**: Deceptive visuals
- **Summoning**: Portal animations

### Environment Controls
- Destroy barrels and trees
- Create explosion effects
- Change weather conditions
- Adjust time of day
- Enable day/night cycle

### Camera & Quality
- Multiple camera angles
- Quality settings (Low/Medium/High)
- Performance monitoring

## 🔧 Performance Features

### Automatic Optimization
- Dynamic quality adjustment based on FPS
- LOD (Level of Detail) system
- Particle count limits
- Memory management

### Performance Monitoring
- Real-time FPS counter
- Draw call tracking
- Memory usage monitoring
- Active particle counting

### Quality Settings
- **Low**: Reduced particles, lower resolution shadows
- **Medium**: Balanced performance and quality
- **High**: Maximum visual quality

## 📁 Project Structure

```
src/
├── core/                   # Core engine components
│   ├── Scene.ts           # 3D scene management
│   └── CombatEffectsEngine.ts # Main engine
├── animations/            # Character animation system
│   └── CharacterAnimator.ts
├── effects/              # Visual effects systems
│   ├── ParticleSystem.ts  # Particle engine
│   └── SpellEffects.ts    # Spell visualization
├── systems/              # Game systems
│   ├── CombatFeedbackSystem.ts
│   └── EnvironmentalSystem.ts
└── types/                # TypeScript definitions
    └── index.ts
```

## 🛠️ Technologies Used

- **Three.js**: 3D graphics and WebGL rendering
- **TypeScript**: Type-safe JavaScript
- **GSAP**: Animation library
- **Vite**: Build tool and development server
- **WebGL**: Hardware-accelerated graphics

## 🎯 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requires WebGL 2.0 support for optimal performance.

## 📝 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📞 Support

For questions, issues, or suggestions:
- Create an issue on GitHub
- Check the documentation
- Review the demo code examples

---

**Built with ❤️ for D&D enthusiasts and game developers**