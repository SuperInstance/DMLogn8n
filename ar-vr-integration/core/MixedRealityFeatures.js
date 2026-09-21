/**
 * Mixed Reality Features for D&D
 * Handles holographic NPCs, environmental effects, portal visualization, and magic interactions
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export class MixedRealityFeatures {
  constructor(arvrCore, options = {}) {
    this.arvrCore = arvrCore;
    this.options = {
      enableHolograms: options.enableHolograms !== false,
      enableEnvironmentalEffects: options.enableEnvironmentalEffects !== false,
      enablePortals: options.enablePortals !== false,
      enableMagicItems: options.enableMagicItems !== false,
      enableSpatialAnchors: options.enableSpatialAnchors !== false,
      maxHolograms: options.maxHolograms || 10,
      maxEffects: options.maxEffects || 20,
      ...options
    };

    // Feature systems
    this.hologramManager = new HologramManager(this.arvrCore);
    this.environmentalEffects = new EnvironmentalEffects(this.arvrCore);
    this.portalSystem = new PortalSystem(this.arvrCore);
    this.magicItemViewer = new MagicItemViewer(this.arvrCore);
    this.spatialAnchorManager = new SpatialAnchorManager(this.arvrCore);

    // Active instances
    this.activeHolograms = new Map();
    this.activeEffects = new Map();
    this.activePortals = new Map();
    this.activeMagicItems = new Map();

    // Scene state
    this.isInitialized = false;
    this.currentEnvironment = 'dungeon';
    this.lightingConditions = 'normal';

    this.eventListeners = new Map();
  }

  async initialize() {
    try {
      console.log('Initializing Mixed Reality Features...');

      // Initialize all feature systems
      await this.hologramManager.initialize();
      await this.environmentalEffects.initialize();
      await this.portalSystem.initialize();
      await this.magicItemViewer.initialize();
      await this.spatialAnchorManager.initialize();

      // Setup event handlers
      this.setupEventHandlers();

      // Load default assets
      await this.loadDefaultAssets();

      this.isInitialized = true;
      this.emit('initialized');

      console.log('Mixed Reality Features initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize Mixed Reality Features:', error);
      this.emit('error', error);
      return false;
    }
  }

  async loadDefaultAssets() {
    // Load holographic character models
    await this.hologramManager.loadCharacterModels([
      'wizard', 'warrior', 'rogue', 'cleric', 'npc_merchant', 'npc_guard'
    ]);

    // Load environmental effect templates
    await this.environmentalEffects.loadEffectTemplates([
      'torch_light', 'magical_aura', 'fog', 'rain', 'snow', 'lava_glow'
    ]);

    // Load portal effects
    await this.portalSystem.loadPortalTypes([
      'magic_circle', 'dimensional_rift', 'nature_portal', 'shadow_gate'
    ]);

    // Load magic item models
    await this.magicItemViewer.loadItemModels([
      'sword_flame', 'staff_arcane', 'ring_invisibility', 'amulet_protection',
      'potion_healing', 'scroll_spell', 'crystal_power'
    ]);
  }

  setupEventHandlers() {
    this.hologramManager.on('hologramCreated', (data) => {
      this.activeHolograms.set(data.id, data);
      this.emit('hologramCreated', data);
    });

    this.environmentalEffects.on('effectStarted', (data) => {
      this.activeEffects.set(data.id, data);
      this.emit('environmentalEffectStarted', data);
    });

    this.portalSystem.on('portalCreated', (data) => {
      this.activePortals.set(data.id, data);
      this.emit('portalCreated', data);
    });

    this.magicItemViewer.on('itemViewed', (data) => {
      this.activeMagicItems.set(data.id, data);
      this.emit('magicItemViewed', data);
    });
  }

  // Holographic NPCs
  async spawnHolographicNPC(npcData, position) {
    if (!this.options.enableHolograms) {
      throw new Error('Holograms are disabled');
    }

    if (this.activeHolograms.size >= this.options.maxHolograms) {
      throw new Error('Maximum holograms reached');
    }

    const hologram = await this.hologramManager.createHologram(npcData, position);
    return hologram;
  }

  updateHologramDialogue(hologramId, dialogueText, duration = 5000) {
    const hologram = this.activeHolograms.get(hologramId);
    if (hologram) {
      return this.hologramManager.updateDialogue(hologram, dialogueText, duration);
    }
    return false;
  }

  makeHologramFollow(hologramId, target, offset = new THREE.Vector3(0, 0, 0)) {
    const hologram = this.activeHolograms.get(hologramId);
    if (hologram) {
      return this.hologramManager.setFollowTarget(hologram, target, offset);
    }
    return false;
  }

  // Environmental Effects
  createEnvironmentalEffect(effectType, position, options = {}) {
    if (!this.options.enableEnvironmentalEffects) {
      throw new Error('Environmental effects are disabled');
    }

    return this.environmentalEffects.createEffect(effectType, position, options);
  }

  setEnvironmentLighting(conditions, intensity = 1.0) {
    this.lightingConditions = conditions;
    return this.environmentalEffects.setLightingConditions(conditions, intensity);
  }

  createAtmosphericWeather(weatherType, intensity = 1.0) {
    const weatherEffects = {
      'rain': () => this.environmentalEffects.createRain(intensity),
      'snow': () => this.environmentalEffects.createSnow(intensity),
      'fog': () => this.environmentalEffects.createFog(intensity),
      'mist': () => this.environmentalEffects.createMist(intensity),
      'magical_storm': () => this.environmentalEffects.createMagicalStorm(intensity)
    };

    if (weatherEffects[weatherType]) {
      return weatherEffects[weatherType]();
    }
  }

  // Portal System
  createPortal(portalType, position, destination = null, options = {}) {
    if (!this.options.enablePortals) {
      throw new Error('Portals are disabled');
    }

    return this.portalSystem.createPortal(portalType, position, destination, options);
  }

  linkPortals(portal1Id, portal2Id) {
    const portal1 = this.activePortals.get(portal1Id);
    const portal2 = this.activePortals.get(portal2Id);

    if (portal1 && portal2) {
      return this.portalSystem.linkPortals(portal1, portal2);
    }
    return false;
  }

  activatePortal(portalId, destinationScene = null) {
    const portal = this.activePortals.get(portalId);
    if (portal) {
      return this.portalSystem.activatePortal(portal, destinationScene);
    }
    return false;
  }

  // Magic Item Viewer
  inspectMagicItem(itemData, position) {
    if (!this.options.enableMagicItems) {
      throw new Error('Magic item inspection is disabled');
    }

    return this.magicItemViewer.createItemViewer(itemData, position);
  }

  rotateMagicItem(itemId, rotationSpeed = 0.01) {
    const item = this.activeMagicItems.get(itemId);
    if (item) {
      return this.magicItemViewer.setRotationSpeed(item, rotationSpeed);
    }
    return false;
  }

  showItemInfo(itemId, showInfo = true) {
    const item = this.activeMagicItems.get(itemId);
    if (item) {
      return this.magicItemViewer.showInfo(item, showInfo);
    }
    return false;
  }

  // Spatial Anchors
  createSpatialAnchor(position, name, options = {}) {
    if (!this.options.enableSpatialAnchors) {
      throw new Error('Spatial anchors are disabled');
    }

    return this.spatialAnchorManager.createAnchor(position, name, options);
  }

  attachObjectToAnchor(anchorId, object) {
    return this.spatialAnchorManager.attachObject(anchorId, object);
  }

  // Scene transitions
  async transitionToScene(sceneData, transitionType = 'portal') {
    switch (transitionType) {
      case 'portal':
        return this.portalTransition(sceneData);
      case 'fade':
        return this.fadeTransition(sceneData);
      case 'dissolve':
        return this.dissolveTransition(sceneData);
      default:
        return this.instantTransition(sceneData);
    }
  }

  async portalTransition(sceneData) {
    // Create portal effect
    const portal = await this.createPortal('dimensional_rift',
      this.arvrCore.camera.position,
      sceneData
    );

    // Activate portal after delay
    setTimeout(() => {
      this.activatePortal(portal.id);
    }, 1000);

    return portal;
  }

  async fadeTransition(sceneData) {
    // Create fade overlay
    const fadeOverlay = this.createFadeOverlay();

    // Fade out
    await this.animateFade(fadeOverlay, 0, 1, 1000);

    // Load new scene
    await this.loadScene(sceneData);

    // Fade in
    await this.animateFade(fadeOverlay, 1, 0, 1000);

    // Remove overlay
    this.arvrCore.scene.remove(fadeOverlay);

    return true;
  }

  async dissolveTransition(sceneData) {
    // Create dissolve effect
    const dissolveEffect = this.environmentalEffects.createDissolveEffect();

    // Start dissolve
    dissolveEffect.start();

    // Load new scene during dissolve
    setTimeout(async () => {
      await this.loadScene(sceneData);
    }, 500);

    return dissolveEffect;
  }

  async instantTransition(sceneData) {
    return this.loadScene(sceneData);
  }

  createFadeOverlay() {
    const geometry = new THREE.PlaneGeometry(100, 100);
    const material = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide
    });

    const overlay = new THREE.Mesh(geometry, material);
    overlay.position.set(0, 0, -10);
    this.arvrCore.scene.add(overlay);

    return overlay;
  }

  animateFade(overlay, fromOpacity, toOpacity, duration) {
    return new Promise((resolve) => {
      const startTime = Date.now();
      const material = overlay.material;

      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        material.opacity = fromOpacity + (toOpacity - fromOpacity) * progress;

        if (progress < 1) {
          requestAnimationFrame(animate);
        } else {
          resolve();
        }
      };

      animate();
    });
  }

  async loadScene(sceneData) {
    // Clear existing holograms and effects
    this.clearAllFeatures();

    // Load new scene elements
    if (sceneData.holograms) {
      for (const hologramData of sceneData.holograms) {
        await this.spawnHolographicNPC(
          hologramData.npc,
          new THREE.Vector3(hologramData.position.x, hologramData.position.y, hologramData.position.z)
        );
      }
    }

    if (sceneData.effects) {
      for (const effectData of sceneData.effects) {
        this.createEnvironmentalEffect(
          effectData.type,
          new THREE.Vector3(effectData.position.x, effectData.position.y, effectData.position.z),
          effectData.options
        );
      }
    }

    if (sceneData.lighting) {
      this.setEnvironmentLighting(sceneData.lighting.conditions, sceneData.lighting.intensity);
    }

    this.currentEnvironment = sceneData.name || 'unknown';
    this.emit('sceneLoaded', sceneData);
  }

  clearAllFeatures() {
    // Clear holograms
    for (const hologram of this.activeHolograms.values()) {
      this.hologramManager.removeHologram(hologram.id);
    }
    this.activeHolograms.clear();

    // Clear effects
    for (const effect of this.activeEffects.values()) {
      this.environmentalEffects.removeEffect(effect.id);
    }
    this.activeEffects.clear();

    // Clear portals
    for (const portal of this.activePortals.values()) {
      this.portalSystem.removePortal(portal.id);
    }
    this.activePortals.clear();

    // Clear magic items
    for (const item of this.activeMagicItems.values()) {
      this.magicItemViewer.removeItem(item.id);
    }
    this.activeMagicItems.clear();
  }

  // Update loop
  update(deltaTime) {
    if (!this.isInitialized) return;

    // Update all feature systems
    this.hologramManager.update(deltaTime);
    this.environmentalEffects.update(deltaTime);
    this.portalSystem.update(deltaTime);
    this.magicItemViewer.update(deltaTime);
    this.spatialAnchorManager.update(deltaTime);
  }

  // Event system
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => callback(data));
    }
  }

  // Cleanup
  dispose() {
    this.clearAllFeatures();

    // Dispose all feature systems
    this.hologramManager.dispose();
    this.environmentalEffects.dispose();
    this.portalSystem.dispose();
    this.magicItemViewer.dispose();
    this.spatialAnchorManager.dispose();

    this.eventListeners.clear();
    this.isInitialized = false;
  }
}

// Hologram Manager
class HologramManager {
  constructor(arvrCore) {
    this.arvrCore = arvrCore;
    this.holograms = new Map();
    this.loader = new GLTFLoader();
    this.loadedModels = new Map();
    this.characterModels = new Map();
  }

  async initialize() {
    // Setup hologram shader materials
    this.hologramMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        opacity: { value: 0.8 },
        hologramColor: { value: new THREE.Color(0x00ffff) }
      },
      vertexShader: `
        varying vec2 vUv;
        varying vec3 vPosition;

        void main() {
          vUv = uv;
          vPosition = position;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform float opacity;
        uniform vec3 hologramColor;
        varying vec2 vUv;
        varying vec3 vPosition;

        void main() {
          float scanline = sin(vPosition.y * 10.0 + time * 5.0) * 0.5 + 0.5;
          float glitch = sin(vUv.x * 100.0 + time * 10.0) * 0.02;

          vec3 color = hologramColor;
          color *= scanline;
          color += glitch;

          float alpha = opacity * (0.7 + scanline * 0.3);

          gl_FragColor = vec4(color, alpha);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide
    });

    console.log('Hologram Manager initialized');
  }

  async loadCharacterModels(characterTypes) {
    const loadPromises = characterTypes.map(async (type) => {
      try {
        const modelUrl = `/assets/models/characters/${type}_hologram.gltf`;
        const gltf = await this.loadModel(modelUrl);
        this.characterModels.set(type, gltf);
        console.log(`Loaded hologram model: ${type}`);
      } catch (error) {
        console.warn(`Failed to load hologram model ${type}:`, error);
        // Create fallback geometry
        this.createFallbackModel(type);
      }
    });

    await Promise.all(loadPromises);
  }

  async loadModel(url) {
    return new Promise((resolve, reject) => {
      this.loader.load(url, resolve, null, reject);
    });
  }

  createFallbackModel(type) {
    const geometry = new THREE.CapsuleGeometry(0.3, 1.8, 4, 8);
    const material = this.hologramMaterial.clone();
    material.uniforms.hologramColor.value.setHex(0x00ffff);

    const group = new THREE.Group();
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.y = 0.9;
    group.add(mesh);

    const fallbackGltf = { scene: group };
    this.characterModels.set(type, fallbackGltf);
  }

  async createHologram(npcData, position) {
    const id = this.generateId();
    const modelData = this.characterModels.get(npcData.type || 'npc_merchant');

    if (!modelData) {
      throw new Error(`Hologram model not found: ${npcData.type}`);
    }

    // Clone the model
    const model = modelData.scene.clone();
    model.position.copy(position);

    // Apply hologram material to all meshes
    model.traverse((child) => {
      if (child.isMesh) {
        child.material = this.hologramMaterial.clone();
        child.material.uniforms.hologramColor.value.setHex(
          npcData.hologramColor || 0x00ffff
        );
      }
    });

    // Create hologram object
    const hologram = {
      id: id,
      model: model,
      data: npcData,
      position: position.clone(),
      dialogue: null,
      followTarget: null,
      followOffset: new THREE.Vector3(),
      isActive: true,
      animationMixer: null
    };

    // Setup animations if available
    if (modelData.animations && modelData.animations.length > 0) {
      hologram.animationMixer = new THREE.AnimationMixer(model);
      modelData.animations.forEach((clip) => {
        hologram.animationMixer.clipAction(clip);
      });
    }

    this.arvrCore.scene.add(model);
    this.holograms.set(id, hologram);

    // Add subtle floating animation
    this.addFloatingAnimation(hologram);

    return hologram;
  }

  addFloatingAnimation(hologram) {
    const startY = hologram.position.y;
    const floatSpeed = 0.5 + Math.random() * 0.5;
    const floatHeight = 0.1 + Math.random() * 0.1;

    hologram.floatingAnimation = {
      startY: startY,
      floatSpeed: floatSpeed,
      floatHeight: floatHeight
    };
  }

  updateDialogue(hologram, dialogueText, duration) {
    // Create dialogue bubble
    const dialogueBubble = this.createDialogueBubble(dialogueText);
    dialogueBubble.position.copy(hologram.position);
    dialogueBubble.position.y += 2.5;
    this.arvrCore.scene.add(dialogueBubble);

    // Remove after duration
    setTimeout(() => {
      this.arvrCore.scene.remove(dialogueBubble);
    }, duration);

    hologram.dialogue = {
      text: dialogueText,
      bubble: dialogueBubble,
      endTime: Date.now() + duration
    };

    return true;
  }

  createDialogueBubble(text) {
    const group = new THREE.Group();

    // Create background plane
    const geometry = new THREE.PlaneGeometry(2, 0.8);
    const material = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.8
    });

    const background = new THREE.Mesh(geometry, material);
    group.add(background);

    // Create text (simplified - in production would use TextGeometry)
    const textGeometry = new THREE.PlaneGeometry(1.8, 0.6);
    const textMaterial = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.9
    });

    const textMesh = new THREE.Mesh(textGeometry, textMaterial);
    textMesh.position.z = 0.01;
    group.add(textMesh);

    // Always face camera
    group.lookAt(this.arvrCore.camera.position);

    return group;
  }

  setFollowTarget(hologram, target, offset) {
    hologram.followTarget = target;
    hologram.followOffset.copy(offset);
    return true;
  }

  removeHologram(hologramId) {
    const hologram = this.holograms.get(hologramId);
    if (!hologram) return false;

    this.arvrCore.scene.remove(hologram.model);

    if (hologram.dialogue && hologram.dialogue.bubble) {
      this.arvrCore.scene.remove(hologram.dialogue.bubble);
    }

    this.holograms.delete(hologramId);
    return true;
  }

  update(deltaTime) {
    const time = Date.now() * 0.001;

    // Update hologram material uniforms
    this.hologramMaterial.uniforms.time.value = time;

    for (const hologram of this.holograms.values()) {
      // Update floating animation
      if (hologram.floatingAnimation) {
        const float = hologram.floatingAnimation;
        hologram.model.position.y = float.startY +
          Math.sin(time * float.floatSpeed) * float.floatHeight;
      }

      // Update follow target
      if (hologram.followTarget) {
        const targetPos = hologram.followTarget.position || hologram.followTarget;
        hologram.model.position.copy(targetPos).add(hologram.followOffset);
      }

      // Update dialogue bubble
      if (hologram.dialogue && hologram.dialogue.bubble) {
        hologram.dialogue.bubble.position.copy(hologram.model.position);
        hologram.dialogue.bubble.position.y += 2.5;
        hologram.dialogue.bubble.lookAt(this.arvrCore.camera.position);

        // Remove expired dialogue
        if (Date.now() > hologram.dialogue.endTime) {
          this.arvrCore.scene.remove(hologram.dialogue.bubble);
          hologram.dialogue = null;
        }
      }

      // Update animations
      if (hologram.animationMixer) {
        hologram.animationMixer.update(deltaTime);
      }
    }
  }

  generateId() {
    return 'hologram_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  dispose() {
    for (const hologram of this.holograms.values()) {
      this.arvrCore.scene.remove(hologram.model);
    }
    this.holograms.clear();
    this.characterModels.clear();
  }
}

// Environmental Effects
class EnvironmentalEffects {
  constructor(arvrCore) {
    this.arvrCore = arvrCore;
    this.effects = new Map();
    this.particleSystems = new Map();
    this.lights = new Map();
  }

  async initialize() {
    console.log('Environmental Effects initialized');
  }

  async loadEffectTemplates(effectTypes) {
    // Preload effect templates
    for (const type of effectTypes) {
      await this.loadEffectTemplate(type);
    }
  }

  async loadEffectTemplate(type) {
    // Implementation for loading effect templates
    console.log(`Loaded effect template: ${type}`);
  }

  createEffect(type, position, options = {}) {
    const id = this.generateId();
    let effect = null;

    switch (type) {
      case 'torch_light':
        effect = this.createTorchLight(position, options);
        break;
      case 'magical_aura':
        effect = this.createMagicalAura(position, options);
        break;
      case 'fog':
        effect = this.createFogEffect(position, options);
        break;
      case 'rain':
        effect = this.createRainEffect(position, options);
        break;
      case 'snow':
        effect = this.createSnowEffect(position, options);
        break;
      case 'lava_glow':
        effect = this.createLavaGlow(position, options);
        break;
      default:
        console.warn(`Unknown effect type: ${type}`);
        return null;
    }

    if (effect) {
      effect.id = id;
      effect.type = type;
      effect.position = position.clone();
      this.effects.set(id, effect);
      this.arvrCore.scene.add(effect.group || effect);
    }

    return effect;
  }

  createTorchLight(position, options) {
    const group = new THREE.Group();
    group.position.copy(position);

    // Create flame
    const flameGeometry = new THREE.SphereGeometry(0.1, 8, 8);
    const flameMaterial = new THREE.MeshBasicMaterial({
      color: 0xff6b35,
      transparent: true,
      opacity: 0.8
    });

    const flame = new THREE.Mesh(flameGeometry, flameMaterial);
    group.add(flame);

    // Create light
    const light = new THREE.PointLight(0xff6b35, 1, 10);
    light.position.y = 0.2;
    group.add(light);

    // Create particles
    const particles = this.createFireParticles();
    group.add(particles);

    return {
      group: group,
      flame: flame,
      light: light,
      particles: particles,
      intensity: options.intensity || 1.0
    };
  }

  createMagicalAura(position, options) {
    const group = new THREE.Group();
    group.position.copy(position);

    // Create aura mesh
    const geometry = new THREE.SphereGeometry(1, 16, 16);
    const material = new THREE.MeshBasicMaterial({
      color: options.color || 0x9b59b6,
      transparent: true,
      opacity: 0.3,
      side: THREE.BackSide
    });

    const aura = new THREE.Mesh(geometry, material);
    group.add(aura);

    // Create magical particles
    const particles = this.createMagicalParticles(options.color || 0x9b59b6);
    group.add(particles);

    return {
      group: group,
      aura: aura,
      particles: particles,
      color: options.color || 0x9b59b6,
      intensity: options.intensity || 1.0
    };
  }

  createFireParticles() {
    const particleCount = 20;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 0.3;
      positions[i * 3 + 1] = Math.random() * 0.5;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 0.3;

      colors[i * 3] = 1.0;     // R
      colors[i * 3 + 1] = 0.4; // G
      colors[i * 3 + 2] = 0.2; // B
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.05,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });

    return new THREE.Points(geometry, material);
  }

  createMagicalParticles(color) {
    const particleCount = 30;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      const radius = 0.5 + Math.random() * 0.5;

      positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
      positions[i * 3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      positions[i * 3 + 2] = radius * Math.cos(phi);
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      size: 0.03,
      color: color,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(geometry, material);

    // Store particle velocities for animation
    particles.userData.velocities = [];
    for (let i = 0; i < particleCount; i++) {
      particles.userData.velocities.push(new THREE.Vector3(
        (Math.random() - 0.5) * 0.01,
        (Math.random() - 0.5) * 0.01,
        (Math.random() - 0.5) * 0.01
      ));
    }

    return particles;
  }

  createRainEffect(position, options) {
    const particleCount = 100;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 1] = Math.random() * 10;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      size: 0.02,
      color: 0x6bb6ff,
      transparent: true,
      opacity: 0.6
    });

    const rain = new THREE.Points(geometry, material);
    rain.position.copy(position);

    return {
      mesh: rain,
      intensity: options.intensity || 1.0
    };
  }

  createSnowEffect(position, options) {
    const particleCount = 80;
    const geometry = new THREE.BufferGeometry();
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 10;
      positions[i * 3 + 1] = Math.random() * 10;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const material = new THREE.PointsMaterial({
      size: 0.05,
      color: 0xffffff,
      transparent: true,
      opacity: 0.8
    });

    const snow = new THREE.Points(geometry, material);
    snow.position.copy(position);

    return {
      mesh: snow,
      intensity: options.intensity || 1.0
    };
  }

  createLavaGlow(position, options) {
    const light = new THREE.PointLight(0xff4500, 2, 15);
    light.position.copy(position);

    // Add glow effect
    const geometry = new THREE.SphereGeometry(0.5, 16, 16);
    const material = new THREE.MeshBasicMaterial({
      color: 0xff4500,
      transparent: true,
      opacity: 0.3,
      side: THREE.BackSide
    });

    const glow = new THREE.Mesh(geometry, material);
    glow.position.copy(position);

    return {
      light: light,
      glow: glow,
      intensity: options.intensity || 1.0
    };
  }

  setLightingConditions(conditions, intensity) {
    // Adjust scene lighting based on conditions
    const lightingPresets = {
      'normal': { ambient: 0.5, directional: 1.0, color: 0xffffff },
      'dim': { ambient: 0.2, directional: 0.5, color: 0x404040 },
      'bright': { ambient: 0.8, directional: 1.2, color: 0xffffcc },
      'magical': { ambient: 0.4, directional: 0.8, color: 0xcc99ff },
      'fire': { ambient: 0.3, directional: 0.8, color: 0xff6b35 },
      'ice': { ambient: 0.6, directional: 1.0, color: 0xb3d9ff }
    };

    const preset = lightingPresets[conditions] || lightingPresets['normal'];

    if (this.arvrCore.lights) {
      if (this.arvrCore.lights.ambient) {
        this.arvrCore.lights.ambient.intensity = preset.ambient * intensity;
      }
      if (this.arvrCore.lights.directional) {
        this.arvrCore.lights.directional.intensity = preset.directional * intensity;
        this.arvrCore.lights.directional.color.setHex(preset.color);
      }
    }
  }

  removeEffect(effectId) {
    const effect = this.effects.get(effectId);
    if (!effect) return false;

    const object = effect.group || effect.mesh || effect.light || effect.glow;
    if (object) {
      this.arvrCore.scene.remove(object);
    }

    this.effects.delete(effectId);
    return true;
  }

  update(deltaTime) {
    const time = Date.now() * 0.001;

    for (const effect of this.effects.values()) {
      if (effect.flame) {
        // Animate flame
        effect.flame.scale.setScalar(
          1 + Math.sin(time * 5) * 0.1
        );
        effect.flame.material.opacity = 0.8 + Math.sin(time * 3) * 0.2;
      }

      if (effect.light) {
        // Animate light intensity
        effect.light.intensity = effect.intensity * (1 + Math.sin(time * 2) * 0.2);
      }

      if (effect.particles) {
        // Animate particles
        const positions = effect.particles.geometry.attributes.position.array;
        const velocities = effect.particles.userData.velocities;

        if (velocities) {
          for (let i = 0; i < positions.length / 3; i++) {
            positions[i * 3] += velocities[i].x;
            positions[i * 3 + 1] += velocities[i].y;
            positions[i * 3 + 2] += velocities[i].z;

            // Reset particles that go too far
            if (Math.abs(positions[i * 3]) > 1 ||
                Math.abs(positions[i * 3 + 1]) > 1 ||
                Math.abs(positions[i * 3 + 2]) > 1) {
              positions[i * 3] = (Math.random() - 0.5) * 0.3;
              positions[i * 3 + 1] = 0;
              positions[i * 3 + 2] = (Math.random() - 0.5) * 0.3;
            }
          }
          effect.particles.geometry.attributes.position.needsUpdate = true;
        }
      }

      if (effect.aura) {
        // Animate aura
        effect.aura.scale.setScalar(
          1 + Math.sin(time) * 0.1
        );
        effect.aura.material.opacity = 0.3 + Math.sin(time * 0.5) * 0.1;
      }

      if (effect.mesh && effect.intensity) {
        // Animate weather effects
        const positions = effect.mesh.geometry.attributes.position.array;

        for (let i = 0; i < positions.length / 3; i++) {
          positions[i * 3 + 1] -= 0.1 * effect.intensity;

          // Reset particles that fall too low
          if (positions[i * 3 + 1] < -5) {
            positions[i * 3 + 1] = 5;
          }
        }
        effect.mesh.geometry.attributes.position.needsUpdate = true;
      }
    }
  }

  generateId() {
    return 'effect_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  dispose() {
    for (const effect of this.effects.values()) {
      const object = effect.group || effect.mesh || effect.light || effect.glow;
      if (object) {
        this.arvrCore.scene.remove(object);
      }
    }
    this.effects.clear();
  }
}

// Portal System
class PortalSystem {
  constructor(arvrCore) {
    this.arvrCore = arvrCore;
    this.portals = new Map();
    this.portalTypes = new Map();
  }

  async initialize() {
    console.log('Portal System initialized');
  }

  async loadPortalTypes(portalTypes) {
    for (const type of portalTypes) {
      await this.loadPortalType(type);
    }
  }

  async loadPortalType(type) {
    console.log(`Loaded portal type: ${type}`);
  }

  createPortal(type, position, destination, options = {}) {
    const id = this.generateId();
    const group = new THREE.Group();
    group.position.copy(position);

    // Create portal based on type
    let portalMesh = null;

    switch (type) {
      case 'magic_circle':
        portalMesh = this.createMagicCircle();
        break;
      case 'dimensional_rift':
        portalMesh = this.createDimensionalRift();
        break;
      case 'nature_portal':
        portalMesh = this.createNaturePortal();
        break;
      case 'shadow_gate':
        portalMesh = this.createShadowGate();
        break;
      default:
        portalMesh = this.createDefaultPortal();
    }

    group.add(portalMesh);

    const portal = {
      id: id,
      type: type,
      group: group,
      mesh: portalMesh,
      position: position.clone(),
      destination: destination,
      isActive: false,
      linkedPortal: null,
      animationTime: 0
    };

    this.arvrCore.scene.add(group);
    this.portals.set(id, portal);

    return portal;
  }

  createMagicCircle() {
    const group = new THREE.Group();

    // Create outer ring
    const ringGeometry = new THREE.RingGeometry(1, 1.2, 32);
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x9b59b6,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    });

    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = -Math.PI / 2;
    group.add(ring);

    // Create inner glow
    const glowGeometry = new THREE.CircleGeometry(0.9, 32);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: 0x8e44ad,
      transparent: true,
      opacity: 0.4,
      side: THREE.DoubleSide
    });

    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    glow.rotation.x = -Math.PI / 2;
    glow.position.y = 0.01;
    group.add(glow);

    // Add magical symbols
    this.addMagicalSymbols(group);

    return group;
  }

  createDimensionalRift() {
    const group = new THREE.Group();

    // Create rift effect
    const geometry = new THREE.PlaneGeometry(2, 3);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        distortion: { value: 0.1 }
      },
      vertexShader: `
        varying vec2 vUv;

        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float time;
        uniform float distortion;
        varying vec2 vUv;

        void main() {
          vec2 uv = vUv;
          uv.x += sin(uv.y * 10.0 + time * 2.0) * distortion;
          uv.y += cos(uv.x * 8.0 + time * 1.5) * distortion;

          float rift = smoothstep(0.4, 0.6, abs(uv.x - 0.5)) *
                      smoothstep(0.3, 0.7, abs(uv.y - 0.5));

          vec3 color = mix(vec3(0.5, 0.0, 1.0), vec3(0.0, 0.0, 0.5), rift);

          gl_FragColor = vec4(color, 1.0 - rift);
        }
      `,
      transparent: true,
      side: THREE.DoubleSide
    });

    const rift = new THREE.Mesh(geometry, material);
    group.add(rift);

    return group;
  }

  createNaturePortal() {
    const group = new THREE.Group();

    // Create vine circle
    const segments = 20;
    for (let i = 0; i < segments; i++) {
      const angle = (i / segments) * Math.PI * 2;
      const nextAngle = ((i + 1) / segments) * Math.PI * 2;

      const points = [
        new THREE.Vector3(Math.cos(angle) * 1.1, 0, Math.sin(angle) * 1.1),
        new THREE.Vector3(Math.cos(nextAngle) * 1.1, 0, Math.sin(nextAngle) * 1.1)
      ];

      const geometry = new THREE.TubeGeometry(
        new THREE.CatmullRomCurve3(points),
        1, 0.1, 8, false
      );

      const material = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setHSL(0.3, 0.7, 0.4),
        transparent: true,
        opacity: 0.8
      });

      const vine = new THREE.Mesh(geometry, material);
      group.add(vine);
    }

    // Add leaves
    this.addLeaves(group);

    return group;
  }

  createShadowGate() {
    const group = new THREE.Group();

    // Create dark portal
    const geometry = new THREE.CircleGeometry(1, 32);
    const material = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.9,
      side: THREE.DoubleSide
    });

    const portal = new THREE.Mesh(geometry, material);
    portal.rotation.x = -Math.PI / 2;
    group.add(portal);

    // Add shadow effects
    const shadowGeometry = new THREE.PlaneGeometry(2.5, 2.5);
    const shadowMaterial = new THREE.MeshBasicMaterial({
      color: 0x1a1a1a,
      transparent: true,
      opacity: 0.5,
      side: THREE.DoubleSide
    });

    const shadow = new THREE.Mesh(shadowGeometry, shadowMaterial);
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.y = -0.01;
    group.add(shadow);

    return group;
  }

  createDefaultPortal() {
    const geometry = new THREE.RingGeometry(0.8, 1.2, 32);
    const material = new THREE.MeshBasicMaterial({
      color: 0x4ecdc4,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    });

    const portal = new THREE.Mesh(geometry, material);
    portal.rotation.x = -Math.PI / 2;

    return portal;
  }

  addMagicalSymbols(group) {
    const symbolCount = 6;
    const radius = 1.0;

    for (let i = 0; i < symbolCount; i++) {
      const angle = (i / symbolCount) * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;

      const geometry = new THREE.PlaneGeometry(0.2, 0.2);
      const material = new THREE.MeshBasicMaterial({
        color: 0xffd700,
        transparent: true,
        opacity: 0.8
      });

      const symbol = new THREE.Mesh(geometry, material);
      symbol.position.set(x, 0.01, z);
      symbol.lookAt(0, 10, 0);
      group.add(symbol);
    }
  }

  addLeaves(group) {
    const leafCount = 12;

    for (let i = 0; i < leafCount; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 0.8 + Math.random() * 0.4;

      const geometry = new THREE.PlaneGeometry(0.1, 0.15);
      const material = new THREE.MeshBasicMaterial({
        color: new THREE.Color().setHSL(0.3, 0.6, 0.4 + Math.random() * 0.2),
        transparent: true,
        opacity: 0.8,
        side: THREE.DoubleSide
      });

      const leaf = new THREE.Mesh(geometry, material);
      leaf.position.set(
        Math.cos(angle) * radius,
        Math.random() * 0.2 - 0.1,
        Math.sin(angle) * radius
      );
      leaf.rotation.y = Math.random() * Math.PI * 2;
      leaf.rotation.z = Math.random() * 0.5 - 0.25;
      group.add(leaf);
    }
  }

  linkPortals(portal1, portal2) {
    portal1.linkedPortal = portal2;
    portal2.linkedPortal = portal1;
    return true;
  }

  activatePortal(portal, destinationScene) {
    portal.isActive = true;
    portal.destination = destinationScene;

    // Add activation effects
    this.addPortalActivationEffects(portal);

    return true;
  }

  addPortalActivationEffects(portal) {
    // Create particle effects around portal
    const particleGeometry = new THREE.BufferGeometry();
    const particleCount = 50;
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount; i++) {
      const angle = (i / particleCount) * Math.PI * 2;
      const radius = 1.5 + Math.random() * 0.5;

      positions[i * 3] = Math.cos(angle) * radius;
      positions[i * 3 + 1] = Math.random() * 0.5;
      positions[i * 3 + 2] = Math.sin(angle) * radius;
    }

    particleGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

    const particleMaterial = new THREE.PointsMaterial({
      size: 0.05,
      color: portal.type === 'shadow_gate' ? 0x4a4a4a : 0x9b59b6,
      transparent: true,
      opacity: 0.8,
      blending: THREE.AdditiveBlending
    });

    const particles = new THREE.Points(particleGeometry, particleMaterial);
    portal.group.add(particles);
    portal.particles = particles;
  }

  removePortal(portalId) {
    const portal = this.portals.get(portalId);
    if (!portal) return false;

    this.arvrCore.scene.remove(portal.group);
    this.portals.delete(portalId);
    return true;
  }

  update(deltaTime) {
    const time = Date.now() * 0.001;

    for (const portal of this.portals.values()) {
      portal.animationTime += deltaTime;

      // Rotate magical symbols
      if (portal.group.children.length > 1) {
        portal.group.children.forEach((child, index) => {
          if (index > 0 && child.isMesh) {
            child.rotation.z += 0.01;
          }
        });
      }

      // Animate particles
      if (portal.particles) {
        const positions = portal.particles.geometry.attributes.position.array;

        for (let i = 0; i < positions.length / 3; i++) {
          const angle = Math.atan2(positions[i * 3 + 2], positions[i * 3]);
          const radius = Math.sqrt(positions[i * 3] ** 2 + positions[i * 3 + 2] ** 2);

          const newRadius = radius + Math.sin(time * 2 + i) * 0.01;
          positions[i * 3] = Math.cos(angle) * newRadius;
          positions[i * 3 + 2] = Math.sin(angle) * newRadius;
          positions[i * 3 + 1] += Math.sin(time * 3 + i) * 0.005;
        }

        portal.particles.geometry.attributes.position.needsUpdate = true;
      }

      // Animate shader-based portals
      if (portal.mesh && portal.mesh.material && portal.mesh.material.uniforms) {
        if (portal.mesh.material.uniforms.time) {
          portal.mesh.material.uniforms.time.value = time;
        }
      }
    }
  }

  generateId() {
    return 'portal_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  dispose() {
    for (const portal of this.portals.values()) {
      this.arvrCore.scene.remove(portal.group);
    }
    this.portals.clear();
  }
}

// Magic Item Viewer
class MagicItemViewer {
  constructor(arvrCore) {
    this.arvrCore = arvrCore;
    this.items = new Map();
    this.itemModels = new Map();
    this.loader = new GLTFLoader();
  }

  async initialize() {
    console.log('Magic Item Viewer initialized');
  }

  async loadItemModels(itemTypes) {
    for (const type of itemTypes) {
      await this.loadItemModel(type);
    }
  }

  async loadItemModel(type) {
    try {
      const modelUrl = `/assets/models/items/${type}.gltf`;
      const gltf = await this.loadModel(modelUrl);
      this.itemModels.set(type, gltf);
      console.log(`Loaded item model: ${type}`);
    } catch (error) {
      console.warn(`Failed to load item model ${type}:`, error);
      this.createFallbackItemModel(type);
    }
  }

  async loadModel(url) {
    return new Promise((resolve, reject) => {
      this.loader.load(url, resolve, null, reject);
    });
  }

  createFallbackItemModel(type) {
    const geometry = new THREE.BoxGeometry(0.3, 0.3, 0.3);
    const material = new THREE.MeshStandardMaterial({
      color: this.getItemColor(type),
      metalness: 0.8,
      roughness: 0.2
    });

    const item = new THREE.Mesh(geometry, material);
    const fallbackGltf = { scene: item };
    this.itemModels.set(type, fallbackGltf);
  }

  getItemColor(type) {
    const colors = {
      'sword_flame': 0xff6b35,
      'staff_arcane': 0x9b59b6,
      'ring_invisibility': 0x95afc0,
      'amulet_protection': 0xf39c12,
      'potion_healing': 0x2ecc71,
      'scroll_spell': 0xf1c40f,
      'crystal_power': 0x3498db
    };
    return colors[type] || 0x95afc0;
  }

  createItemViewer(itemData, position) {
    const id = this.generateId();
    const modelData = this.itemModels.get(itemData.type || 'crystal_power');

    if (!modelData) {
      throw new Error(`Item model not found: ${itemData.type}`);
    }

    // Clone the model
    const model = modelData.scene.clone();
    model.position.copy(position);
    model.scale.setScalar(0.1);

    // Create item viewer group
    const group = new THREE.Group();
    group.add(model);

    // Create info panel
    const infoPanel = this.createInfoPanel(itemData);
    infoPanel.position.y = 0.5;
    group.add(infoPanel);

    // Create glow effect
    const glow = this.createItemGlow(itemData.rarity || 'common');
    glow.position.copy(position);
    group.add(glow);

    const item = {
      id: id,
      type: itemData.type,
      data: itemData,
      model: model,
      group: group,
      infoPanel: infoPanel,
      glow: glow,
      position: position.clone(),
      rotationSpeed: 0.01,
      isShowingInfo: true
    };

    this.arvrCore.scene.add(group);
    this.items.set(id, item);

    // Start rotation animation
    this.animateItemRotation(item);

    return item;
  }

  createInfoPanel(itemData) {
    const group = new THREE.Group();

    // Create background
    const geometry = new THREE.PlaneGeometry(1.5, 1);
    const material = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.8
    });

    const background = new THREE.Mesh(geometry, material);
    group.add(background);

    // Create text elements (simplified - would use TextGeometry in production)
    const titleGeometry = new THREE.PlaneGeometry(1.3, 0.2);
    const titleMaterial = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.9
    });

    const title = new THREE.Mesh(titleGeometry, titleMaterial);
    title.position.y = 0.3;
    group.add(title);

    const descriptionGeometry = new THREE.PlaneGeometry(1.3, 0.4);
    const descriptionMaterial = new THREE.MeshBasicMaterial({
      color: 0xcccccc,
      transparent: true,
      opacity: 0.8
    });

    const description = new THREE.Mesh(descriptionGeometry, descriptionMaterial);
    description.position.y = 0;
    group.add(description);

    // Always face camera
    group.userData.alwaysFaceCamera = true;

    return group;
  }

  createItemGlow(rarity) {
    const colors = {
      'common': 0x95afc0,
      'uncommon': 0x2ecc71,
      'rare': 0x3498db,
      'epic': 0x9b59b6,
      'legendary': 0xf39c12
    };

    const geometry = new THREE.SphereGeometry(0.3, 16, 16);
    const material = new THREE.MeshBasicMaterial({
      color: colors[rarity] || colors['common'],
      transparent: true,
      opacity: 0.3,
      side: THREE.BackSide
    });

    const glow = new THREE.Mesh(geometry, material);
    return glow;
  }

  animateItemRotation(item) {
    const animate = () => {
      if (!item.model.parent) return;

      item.model.rotation.y += item.rotationSpeed;

      // Animate glow
      if (item.glow) {
        const pulse = Math.sin(Date.now() * 0.002) * 0.1 + 0.9;
        item.glow.scale.setScalar(pulse);
        item.glow.material.opacity = 0.2 + Math.sin(Date.now() * 0.003) * 0.1;
      }

      // Face info panel to camera
      if (item.infoPanel && item.infoPanel.userData.alwaysFaceCamera) {
        item.infoPanel.lookAt(this.arvrCore.camera.position);
      }

      requestAnimationFrame(animate);
    };

    animate();
  }

  setRotationSpeed(item, speed) {
    item.rotationSpeed = speed;
    return true;
  }

  showInfo(item, showInfo = true) {
    item.isShowingInfo = showInfo;
    item.infoPanel.visible = showInfo;
    return true;
  }

  removeItem(itemId) {
    const item = this.items.get(itemId);
    if (!item) return false;

    this.arvrCore.scene.remove(item.group);
    this.items.delete(itemId);
    return true;
  }

  update(deltaTime) {
    // Items are animated individually in their own animation loops
  }

  generateId() {
    return 'item_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  dispose() {
    for (const item of this.items.values()) {
      this.arvrCore.scene.remove(item.group);
    }
    this.items.clear();
    this.itemModels.clear();
  }
}

// Spatial Anchor Manager
class SpatialAnchorManager {
  constructor(arvrCore) {
    this.arvrCore = arvrCore;
    this.anchors = new Map();
  }

  async initialize() {
    console.log('Spatial Anchor Manager initialized');
  }

  createAnchor(position, name, options = {}) {
    const id = this.generateId();

    const anchor = {
      id: id,
      name: name,
      position: position.clone(),
      attachedObjects: [],
      isPersistent: options.persistent || false,
      confidence: 1.0
    };

    // Create visual representation
    const anchorVisual = this.createAnchorVisual();
    anchorVisual.position.copy(position);
    anchor.visual = anchorVisual;

    this.arvrCore.scene.add(anchorVisual);
    this.anchors.set(id, anchor);

    return anchor;
  }

  createAnchorVisual() {
    const geometry = new THREE.SphereGeometry(0.05, 16, 16);
    const material = new THREE.MeshBasicMaterial({
      color: 0x4ecdc4,
      transparent: true,
      opacity: 0.8
    });

    const anchor = new THREE.Mesh(geometry, material);

    // Add rings
    const ringGeometry = new THREE.RingGeometry(0.1, 0.15, 32);
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x4ecdc4,
      transparent: true,
      opacity: 0.5,
      side: THREE.DoubleSide
    });

    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
    ring.rotation.x = -Math.PI / 2;
    anchor.add(ring);

    return anchor;
  }

  attachObject(anchorId, object) {
    const anchor = this.anchors.get(anchorId);
    if (!anchor) return false;

    anchor.attachedObjects.push(object);

    // Set object's parent to anchor
    object.position.sub(anchor.position);
    anchor.visual.add(object);

    return true;
  }

  removeAnchor(anchorId) {
    const anchor = this.anchors.get(anchorId);
    if (!anchor) return false;

    // Move attached objects back to main scene
    anchor.attachedObjects.forEach(object => {
      object.position.add(anchor.position);
      this.arvrCore.scene.add(object);
    });

    this.arvrCore.scene.remove(anchor.visual);
    this.anchors.delete(anchorId);
    return true;
  }

  update(deltaTime) {
    const time = Date.now() * 0.001;

    for (const anchor of this.anchors.values()) {
      if (anchor.visual) {
        // Animate anchor visual
        anchor.visual.rotation.y += 0.01;

        // Pulse effect
        const pulse = Math.sin(time * 2) * 0.1 + 0.9;
        anchor.visual.scale.setScalar(pulse);
      }
    }
  }

  generateId() {
    return 'anchor_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  dispose() {
    for (const anchor of this.anchors.values()) {
      this.arvrCore.scene.remove(anchor.visual);
    }
    this.anchors.clear();
  }
}

export default MixedRealityFeatures;