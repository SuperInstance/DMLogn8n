# D&D AR/VR Integration System

A cutting-edge AR/VR integration system that brings Dungeons & Dragons into mixed reality with immersive experiences. This comprehensive solution provides virtual tabletops, AR character views, holographic NPCs, and cross-platform support for Meta Quest, HoloLens, ARKit, and ARCore devices.

## 🎯 Features

### VR D&D Tabletop
- **Virtual Tabletop**: Immersive VR environment with hand tracking
- **3D Miniatures**: Physics-based character miniatures with detailed animations
- **Immersive Dungeons**: Richly detailed environments with dynamic lighting
- **Spell Casting**: Hand gesture-based spell casting with spectacular visual effects
- **Voice Chat**: Spatial audio communication system with 3D positioning

### AR Character View
- **AR Character Sheets**: Interactive character stats displayed in real space
- **Virtual Dice**: 3D dice rolling on real tabletop surfaces
- **Spell Effects**: Stunning visualizations in your physical environment
- **Monster Visualization**: See creatures through your device camera
- **Location-Based Adventures**: AR quests triggered by real-world locations

### Mixed Reality Features
- **Holographic NPCs**: Interactive game masters and characters in your space
- **Environmental Effects**: Dynamic weather, lighting, and atmospheric changes
- **Virtual Treasure**: Interactive 3D items you can inspect and manipulate
- **Magic Item Inspection**: Examine equipment with detailed 360° views
- **Portal Visualization**: Seamless transitions between game scenes

### Cross-Platform Support
- **Meta Quest (Oculus)**: Full VR support with hand tracking
- **Microsoft HoloLens**: Advanced AR with spatial mapping
- **ARKit (iOS)**: Native iOS AR experiences
- **ARCore (Android)**: Android AR with plane detection
- **WebXR Browser**: Browser-based VR/AR without additional apps

### Performance & Comfort
- **90 FPS Target**: Optimized for smooth, comfortable VR experiences
- **Adaptive Quality**: Dynamic performance scaling based on device capabilities
- **Efficient Streaming**: Smart asset loading and caching
- **Latency Minimization**: Motion prediction and input optimization
- **Comfort Settings**: Snap turning, vignettes, and motion sickness prevention

## 🏗️ Architecture

```
ar-vr-integration/
├── webxr/                    # WebXR/Three.js implementation
│   ├── src/
│   │   ├── VRTabletop.js     # Main VR tabletop experience
│   │   ├── ARCharacterView.js # AR character viewing system
│   │   └── components/       # VR/AR components
│   ├── public/               # HTML templates and assets
│   └── dist/                 # Built web application
├── unity/                    # Unity VR plugin
│   ├── Assets/Scripts/       # Unity C# scripts
│   └── ProjectSettings/      # Unity configuration
├── core/                     # Core systems and utilities
│   ├── ARVRCore.js          # Base AR/VR framework
│   ├── MixedRealityFeatures.js # Holograms and effects
│   ├── CrossPlatformSupport.js # Device-specific handling
│   └── PerformanceOptimization.js # FPS and comfort settings
├── assets/                   # 3D models, textures, audio
└── scripts/                  # Build and deployment scripts
```

## 🚀 Quick Start

### WebXR Version
1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Development Server**
   ```bash
   npm run dev
   ```

3. **Build for Production**
   ```bash
   npm run build
   ```

4. **Launch Web Server**
   ```bash
   npm run serve
   ```

### Unity Version
1. **Open Unity Project**
   - Open the `unity` folder in Unity 2021.3 LTS or later
   - Import the XR Plugin Management package
   - Configure VR/AR settings for your target platform

2. **Build Settings**
   - Switch platform to your target (Android, iOS, Windows)
   - Configure XR plug-in providers
   - Build and deploy to device

## 🎮 Usage Examples

### WebXR VR Tabletop
```javascript
import { VRTabletop } from './webxr/src/VRTabletop.js';

// Initialize VR tabletop
const tabletop = new VRTabletop(document.body, {
  enableVR: true,
  enableHandTracking: true,
  maxPlayers: 6,
  tabletopSize: { width: 8, height: 8 }
});

await tabletop.initialize();

// Add players
const player = tabletop.addPlayer({
  name: "Aldric Stormwind",
  class: "Wizard",
  level: 5
});

// Cast spells
tabletop.castSpell('fireball', targetPosition);

// Roll dice
tabletop.rollDice(20);
```

### AR Character View
```javascript
import { ARCharacterView } from './webxr/src/ARCharacterView.js';

// Initialize AR view
const arView = new ARCharacterView(document.body, {
  enablePlaneDetection: true,
  enableLightEstimation: true
});

await arView.initialize();

// Place character sheet
arView.placeCharacterSheet(new THREE.Vector3(0, 1, -2));

// Roll virtual dice on real table
arView.rollVirtualDice(20, 18);

// Cast AR spells
arView.castSpellInAR('fireball', cameraPosition);
```

### Unity Plugin
```csharp
// Initialize D&D Tabletop Manager
public class GameManager : MonoBehaviour
{
    public DNDTabletopManager tabletopManager;

    async void Start()
    {
        // Start VR session
        await tabletopManager.InitializeXR();

        // Add players
        tabletopManager.AddPlayer();

        // Roll dice
        tabletopManager.RollDice(20);
    }
}
```

## 🎯 Platform-Specific Features

### Meta Quest
- Hand tracking with gesture recognition
- Haptic feedback for immersive interactions
- Passthrough camera for mixed reality
- Eye tracking (Quest Pro)
- 90 FPS target with foveated rendering

### Microsoft HoloLens
- Spatial mapping and understanding
- Hand tracking with 26 DOF
- Eye tracking and gaze interaction
- Spatial anchors for persistent objects
- Real-world occlusion

### ARKit (iOS)
- Face tracking for expressive NPCs
- Light estimation for realistic rendering
- Plane detection for object placement
- Image tracking for AR triggers
- People occlusion

### ARCore (Android)
- Environmental understanding
- Cloud anchors for multiplayer
- Augmented images for triggers
- Depth API for realistic occlusion
- Instant placement

## 🛠️ Development

### Core Systems

#### ARVRCore
Base framework providing:
- Device capability detection
- Session management
- Input handling
- Performance monitoring
- Cross-platform abstraction

#### Performance Optimization
- Adaptive quality scaling
- Memory management
- Asset streaming
- Frame rate optimization
- Comfort settings

#### Mixed Reality Features
- Holographic rendering
- Spatial audio
- Environmental effects
- Portal transitions
- Magic item inspection

### Build System

The project uses a modern build system:
- **Webpack** for JavaScript bundling
- **TypeScript** for type safety
- **Three.js** for 3D graphics
- **WebXR** for VR/AR support
- **Unity** for native applications

### Asset Pipeline

3D assets are optimized for different platforms:
- **GLTF** models with Draco compression
- **Texture atlases** for efficient rendering
- **Audio compression** for spatial sound
- **LOD systems** for performance scaling

## 🎨 Asset Creation

### 3D Models
- Use Blender or Maya for model creation
- Export as GLTF with Draco compression
- Include animations for characters
- Create LOD versions for performance

### Audio
- Record spatial audio for immersion
- Use ambisonic formats for 360° sound
- Compress using Opus codec
- Create reverb zones for environments

### Textures
- Use PBR materials for realistic rendering
- Include normal, roughness, and metallic maps
- Optimize texture sizes for target platforms
- Use atlases to reduce draw calls

## 📊 Performance Metrics

### Target Specifications
- **Frame Rate**: 90 FPS (VR), 60 FPS (AR)
- **Latency**: < 20ms motion-to-photon
- **Memory**: < 4GB usage
- **Battery**: 2+ hours continuous use

### Optimization Techniques
- Frustum culling for off-screen objects
- Level of detail (LOD) systems
- Object pooling for frequently used items
- Async asset loading
- Adaptive quality scaling

## 🔧 Configuration

### VR Settings
```javascript
const vrOptions = {
  targetFPS: 90,
  enableHandTracking: true,
  enableSpatialAudio: true,
  comfortMode: 'comfortable',
  movementType: 'snap'
};
```

### AR Settings
```javascript
const arOptions = {
  enablePlaneDetection: true,
  enableLightEstimation: true,
  maxPlacedObjects: 20,
  placementDistance: 2.0
};
```

### Performance Settings
```javascript
const performanceOptions = {
  adaptiveQuality: true,
  targetFrameTime: 11.11, // 90 FPS
  memoryLimit: 2048, // MB
  lodBias: -1.0
};
```

## 🤝 Contributing

We welcome contributions to the D&D AR/VR Integration System! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch
3. **Commit** your changes with clear descriptions
4. **Test** on multiple platforms
5. **Submit** a pull request

### Development Guidelines
- Follow existing code style
- Include unit tests
- Update documentation
- Test performance impact
- Ensure cross-platform compatibility

## 📱 Platform Support

| Platform | VR | AR | Hand Tracking | Eye Tracking | Spatial Audio |
|----------|----|----|---------------|--------------|---------------|
| Meta Quest | ✅ | ❌ | ✅ | ✅ (Pro) | ✅ |
| Quest Pro | ✅ | ✅ | ✅ | ✅ | ✅ |
| HoloLens 2 | ❌ | ✅ | ✅ | ✅ | ✅ |
| iOS (ARKit) | ❌ | ✅ | ❌ | ❌ | ✅ |
| Android (ARCore) | ❌ | ✅ | ❌ | ❌ | ✅ |
| WebXR Browsers | ✅ | ✅ | ✅ | ❌ | ✅ |

## 🚧 Roadmap

### Version 1.0 (Current)
- ✅ Basic VR tabletop
- ✅ AR character view
- ✅ Cross-platform support
- ✅ Performance optimization
- ✅ Unity plugin

### Version 1.1 (Planned)
- 🔄 Multiplayer networking
- 🔄 Advanced spell system
- 🔄 Voice chat integration
- 🔄 Cloud save system
- 🔄 Custom campaign creator

### Version 2.0 (Future)
- 📋 AI dungeon master
- 📋 Procedural generation
- 📋 Blockchain integration
- 📋 Mobile companion app
- 📋 Mod support platform

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Three.js** for 3D graphics framework
- **WebXR** for VR/AR API
- **Unity** for native development
- **D&D Beyond** for inspiration
- The D&D community for feedback and support

## 📞 Support

For support, please:
- Check the [documentation](docs/)
- Search [existing issues](issues)
- Join our [Discord community](https://discord.gg/dnd-arvr)
- Email support@dnd-arvr.com

---

**Built with ❤️ by the D&D AR/VR development team**