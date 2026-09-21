/**
 * 3D Miniature Manager for VR D&D
 * Handles placement, movement, physics, and customization of 3D miniatures
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

export class MiniatureManager {
  constructor(arvrCore, options = {}) {
    this.arvrCore = arvrCore;
    this.options = {
      physics: options.physics || null,
      maxMiniatures: options.maxMiniatures || 50,
      enableCustomization: options.enableCustomization !== false,
      enablePhysics: options.enablePhysics !== false,
      enableAnimations: options.enableAnimations !== false,
      baseScale: options.baseScale || 0.01,
      ...options
    };

    this.miniatures = new Map();
    this.loadedModels = new Map();
    this.loader = null;
    this.dracoLoader = null;
    this.raycaster = new THREE.Raycaster();
    this.selectedMiniature = null;
    this.isDragging = false;
    this.dragOffset = new THREE.Vector3();

    // Predefined miniature types
    this.miniatureTypes = {
      player: {
        modelPath: '/assets/models/characters/player.gltf',
        scale: 1.0,
        animations: ['idle', 'walk', 'attack', 'cast']
      },
      monster: {
        modelPath: '/assets/models/characters/monster.gltf',
        scale: 1.2,
        animations: ['idle', 'attack', 'hurt', 'death']
      },
      npc: {
        modelPath: '/assets/models/characters/npc.gltf',
        scale: 1.0,
        animations: ['idle', 'talk', 'walk']
      },
      object: {
        modelPath: '/assets/models/objects/chest.gltf',
        scale: 1.0,
        animations: ['idle']
      }
    };

    this.setupEventHandlers();
  }

  async initialize() {
    // Setup model loader
    this.loader = new GLTFLoader();

    // Setup Draco loader for compressed models
    this.dracoLoader = new DRACOLoader();
    this.dracoLoader.setDecoderPath('/draco/');
    this.loader.setDRACOLoader(this.dracoLoader);

    // Load default models
    await this.loadDefaultModels();

    console.log('Miniature Manager initialized');
  }

  async loadDefaultModels() {
    const loadPromises = Object.entries(this.miniatureTypes).map(async ([type, config]) => {
      try {
        const gltf = await this.loadModel(config.modelPath);
        this.loadedModels.set(type, {
          gltf: gltf,
          config: config
        });
        console.log(`Loaded model: ${type}`);
      } catch (error) {
        console.warn(`Failed to load model ${type}:`, error);
        // Create fallback geometry
        this.createFallbackModel(type);
      }
    });

    await Promise.all(loadPromises);
  }

  loadModel(url) {
    return new Promise((resolve, reject) => {
      this.loader.load(
        url,
        (gltf) => {
          // Optimize model
          this.optimizeModel(gltf.scene);
          resolve(gltf);
        },
        (progress) => {
          const percent = (progress.loaded / progress.total) * 100;
          console.log(`Loading model progress: ${percent.toFixed(1)}%`);
        },
        (error) => {
          reject(error);
        }
      );
    });
  }

  createFallbackModel(type) {
    const geometry = new THREE.BoxGeometry(0.5, 1, 0.5);
    const material = new THREE.MeshStandardMaterial({
      color: this.getTypeColor(type),
      roughness: 0.7,
      metalness: 0.3
    });

    const mesh = new THREE.Mesh(geometry, material);
    mesh.castShadow = true;
    mesh.receiveShadow = true;

    const fallbackGltf = {
      scene: mesh,
      animations: []
    };

    this.loadedModels.set(type, {
      gltf: fallbackGltf,
      config: this.miniatureTypes[type]
    });
  }

  getTypeColor(type) {
    const colors = {
      player: 0x4ecdc4,
      monster: 0xff6b6b,
      npc: 0xf9ca24,
      object: 0x95afc0
    };
    return colors[type] || 0x888888;
  }

  optimizeModel(model) {
    model.traverse((child) => {
      if (child.isMesh) {
        child.castShadow = true;
        child.receiveShadow = true;

        // Optimize materials
        if (child.material) {
          child.material.needsUpdate = true;

          // Reduce material complexity for performance
          if (child.material.map) {
            child.material.map.anisotropy = 4;
          }
        }
      }
    });

    // Center and normalize model
    const box = new THREE.Box3().setFromObject(model);
    const center = box.getCenter(new THREE.Vector3());
    model.position.sub(center);
  }

  createMiniature(type, options = {}) {
    if (this.miniatures.size >= this.options.maxMiniatures) {
      throw new Error('Maximum number of miniatures reached');
    }

    const modelData = this.loadedModels.get(type);
    if (!modelData) {
      throw new Error(`Model type '${type}' not found`);
    }

    // Clone the model
    const model = modelData.gltf.scene.clone();
    const scale = (options.scale || modelData.config.scale) * this.options.baseScale;
    model.scale.set(scale, scale, scale);

    // Create miniature object
    const miniature = {
      id: this.generateId(),
      type: type,
      model: model,
      position: options.position || new THREE.Vector3(0, 0, 0),
      rotation: options.rotation || new THREE.Euler(0, 0, 0),
      health: options.health || 100,
      maxHealth: options.maxHealth || 100,
      name: options.name || `${type}_${this.miniatures.size + 1}`,
      player: options.player || null,
      isActive: true,
      isInteractive: options.isInteractive !== false,
      animationMixer: null,
      currentAnimation: null,
      physicsBody: null
    };

    // Setup position and rotation
    model.position.copy(miniature.position);
    model.rotation.copy(miniature.rotation);

    // Setup animations
    if (this.options.enableAnimations && modelData.gltf.animations.length > 0) {
      miniature.animationMixer = new THREE.AnimationMixer(model);
      modelData.gltf.animations.forEach((clip) => {
        miniature.animationMixer.clipAction(clip);
      });
    }

    // Setup physics
    if (this.options.enablePhysics && this.options.physics) {
      this.setupPhysics(miniature);
    }

    // Setup interaction
    if (miniature.isInteractive) {
      this.setupInteraction(miniature);
    }

    // Add to scene
    this.arvrCore.scene.add(model);
    this.miniatures.set(miniature.id, miniature);

    this.emit('miniatureCreated', miniature);
    return miniature;
  }

  setupPhysics(miniature) {
    if (!this.options.physics) return;

    // Create physics body based on model bounds
    const box = new THREE.Box3().setFromObject(miniature.model);
    const size = box.getSize(new THREE.Vector3());

    const body = this.options.physics.createBox({
      width: size.x,
      height: size.y,
      depth: size.z,
      mass: 1,
      position: miniature.position,
      restitution: 0.3,
      friction: 0.8
    });

    miniature.physicsBody = body;
    this.options.physics.addBody(body);
  }

  setupInteraction(miniature) {
    // Add hover effect
    const originalMaterial = miniature.model.material;
    const hoverMaterial = originalMaterial.clone();
    hoverMaterial.emissive = new THREE.Color(0x444444);

    miniature.model.userData = {
      miniature: miniature,
      originalMaterial: originalMaterial,
      hoverMaterial: hoverMaterial,
      onHover: () => {
        if (originalMaterial) {
          originalMaterial.emissive = new THREE.Color(0x444444);
        }
      },
      onHoverEnd: () => {
        if (originalMaterial) {
          originalMaterial.emissive = new THREE.Color(0x000000);
        }
      }
    };

    this.arvrCore.addInteractiveObject(miniature.model);
  }

  moveMiniature(miniatureId, position, rotation = null) {
    const miniature = this.miniatures.get(miniatureId);
    if (!miniature) return false;

    // Update position
    miniature.position.copy(position);
    miniature.model.position.copy(position);

    // Update physics body
    if (miniature.physicsBody) {
      this.options.physics.setBodyPosition(miniature.physicsBody, position);
    }

    // Update rotation if provided
    if (rotation) {
      miniature.rotation.copy(rotation);
      miniature.model.rotation.copy(rotation);
    }

    this.emit('miniatureMoved', { miniature, position, rotation });
    return true;
  }

  rotateMiniature(miniatureId, rotation) {
    const miniature = this.miniatures.get(miniatureId);
    if (!miniature) return false;

    miniature.rotation.copy(rotation);
    miniature.model.rotation.copy(rotation);

    this.emit('miniatureRotated', { miniature, rotation });
    return true;
  }

  setMiniatureHealth(miniatureId, health, maxHealth = null) {
    const miniature = this.miniatures.get(miniatureId);
    if (!miniature) return false;

    const oldHealth = miniature.health;
    miniature.health = Math.max(0, Math.min(health, miniature.maxHealth));

    if (maxHealth) {
      miniature.maxHealth = maxHealth;
    }

    // Play hurt animation if damaged
    if (miniature.health < oldHealth && miniature.animationMixer) {
      this.playAnimation(miniature, 'hurt');
    }

    // Play death animation if health reaches 0
    if (miniature.health === 0 && miniature.animationMixer) {
      this.playAnimation(miniature, 'death');
      miniature.isActive = false;
    }

    this.emit('healthChanged', { miniature, health: miniature.health, maxHealth: miniature.maxHealth });
    return true;
  }

  playAnimation(miniature, animationName, loop = false) {
    if (!miniature.animationMixer) return false;

    const action = miniature.animationMixer.clipAction(animationName);
    if (action) {
      if (miniature.currentAnimation) {
        miniature.currentAnimation.stop();
      }

      action.setLoop(loop ? THREE.LoopRepeat : THREE.LoopOnce);
      action.play();
      miniature.currentAnimation = action;

      this.emit('animationPlayed', { miniature, animationName, loop });
      return true;
    }

    return false;
  }

  selectMiniature(miniatureId) {
    const miniature = this.miniatures.get(miniatureId);
    if (!miniature) return false;

    // Deselect previous
    if (this.selectedMiniature) {
      this.deselectMiniature();
    }

    this.selectedMiniature = miniature;

    // Add selection effect
    this.addSelectionEffect(miniature);

    this.emit('miniatureSelected', miniature);
    return true;
  }

  deselectMiniature() {
    if (!this.selectedMiniature) return false;

    this.removeSelectionEffect(this.selectedMiniature);
    const previouslySelected = this.selectedMiniature;
    this.selectedMiniature = null;

    this.emit('miniatureDeselected', previouslySelected);
    return true;
  }

  addSelectionEffect(miniature) {
    // Create selection ring
    const geometry = new THREE.RingGeometry(0.6, 0.8, 32);
    const material = new THREE.MeshBasicMaterial({
      color: 0x4ecdc4,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.6
    });

    const ring = new THREE.Mesh(geometry, material);
    ring.position.copy(miniature.position);
    ring.position.y += 0.01;
    ring.rotation.x = -Math.PI / 2;

    this.arvrCore.scene.add(ring);
    miniature.selectionRing = ring;

    // Animate ring
    this.animateSelectionRing(ring);
  }

  animateSelectionRing(ring) {
    const animate = () => {
      if (!ring.parent) return;

      ring.rotation.z += 0.02;
      ring.material.opacity = 0.3 + Math.sin(Date.now() * 0.003) * 0.3;

      requestAnimationFrame(animate);
    };
    animate();
  }

  removeSelectionEffect(miniature) {
    if (miniature.selectionRing) {
      this.arvrCore.scene.remove(miniature.selectionRing);
      miniature.selectionRing = null;
    }
  }

  removeMiniature(miniatureId) {
    const miniature = this.miniatures.get(miniatureId);
    if (!miniature) return false;

    // Remove from scene
    this.arvrCore.scene.remove(miniature.model);

    // Remove selection effect
    this.removeSelectionEffect(miniature);

    // Remove physics body
    if (miniature.physicsBody) {
      this.options.physics.removeBody(miniature.physicsBody);
    }

    // Clean up animation mixer
    if (miniature.animationMixer) {
      miniature.animationMixer.stopAllAction();
    }

    // Remove from interactive objects
    if (miniature.isInteractive) {
      this.arvrCore.removeInteractiveObject(miniature.model);
    }

    this.miniatures.delete(miniatureId);
    this.emit('miniatureRemoved', miniature);
    return true;
  }

  createPlayerMiniature(playerData) {
    const miniature = this.createMiniature('player', {
      name: playerData.name,
      position: new THREE.Vector3(
        playerData.position.x,
        0,
        playerData.position.z
      ),
      scale: 1.0,
      health: 100,
      maxHealth: 100,
      player: playerData,
      isInteractive: true
    });

    // Set player color
    if (playerData.color) {
      miniature.model.traverse((child) => {
        if (child.isMesh && child.material) {
          child.material.color.setHex(playerData.color);
        }
      });
    }

    return miniature;
  }

  placeMiniatures(miniaturesData) {
    const placedMiniatures = [];

    miniaturesData.forEach((data) => {
      try {
        const miniature = this.createMiniature(data.type, data);
        placedMiniatures.push(miniature);
      } catch (error) {
        console.error('Failed to place miniature:', error);
      }
    });

    return placedMiniatures;
  }

  removeAllMiniatures() {
    const miniatureIds = Array.from(this.miniatures.keys());
    miniatureIds.forEach(id => this.removeMiniature(id));
  }

  getMiniatureAtPosition(position, radius = 0.5) {
    for (const miniature of this.miniatures.values()) {
      const distance = miniature.position.distanceTo(position);
      if (distance <= radius) {
        return miniature;
      }
    }
    return null;
  }

  getMiniaturesInArea(center, radius) {
    const miniatures = [];

    for (const miniature of this.miniatures.values()) {
      const distance = miniature.position.distanceTo(center);
      if (distance <= radius) {
        miniatures.push(miniature);
      }
    }

    return miniatures;
  }

  setupEventHandlers() {
    // Handle controller selection
    this.arvrCore.on('objectSelected', (data) => {
      const miniature = data.object.userData.miniature;
      if (miniature) {
        this.selectMiniature(miniature.id);
      }
    });

    // Handle dragging
    this.arvrCore.on('squeeze', (data) => {
      if (this.selectedMiniature) {
        this.isDragging = true;
        this.dragOffset.copy(this.selectedMiniature.position);
      }
    });

    // Handle drag end
    this.arvrCore.on('pinchEnd', (data) => {
      this.isDragging = false;
    });
  }

  update(deltaTime) {
    // Update animations
    for (const miniature of this.miniatures.values()) {
      if (miniature.animationMixer) {
        miniature.animationMixer.update(deltaTime);
      }
    }

    // Update dragging
    if (this.isDragging && this.selectedMiniature) {
      // Get controller position and update miniature
      // This would need implementation based on your input system
    }

    // Update physics sync
    if (this.options.physics) {
      for (const miniature of this.miniatures.values()) {
        if (miniature.physicsBody) {
          const physicsPosition = this.options.physics.getBodyPosition(miniature.physicsBody);
          if (physicsPosition) {
            miniature.position.copy(physicsPosition);
            miniature.model.position.copy(physicsPosition);
          }
        }
      }
    }
  }

  generateId() {
    return 'miniature_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Event system
  on(event, callback) {
    if (!this.eventListeners) {
      this.eventListeners = new Map();
    }
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.eventListeners && this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.eventListeners && this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => callback(data));
    }
  }

  dispose() {
    // Remove all miniatures
    this.removeAllMiniatures();

    // Dispose loaders
    if (this.dracoLoader) {
      this.dracoLoader.dispose();
    }

    // Clear references
    this.loadedModels.clear();
    this.miniatures.clear();
    this.selectedMiniature = null;
  }
}

export default MiniatureManager;