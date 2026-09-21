/**
 * AR Character View for D&D Mobile Experience
 * Provides AR character sheets, virtual dice, and 3D spell effects
 */

import * as THREE from 'three';
import { ARVRCore } from '../../core/ARVRCore.js';
import { ARCharacterSheet } from './components/ARCharacterSheet.js';
import { ARDiceRoller } from './components/ARDiceRoller.js';
import { ARSpellEffects } from './components/ARSpellEffects.js';
import { ARMonsterViewer } from './components/ARMonsterViewer.js';
import { ARCameraController } from './components/ARCameraController.js';
import { ARPlacementSystem } from './components/ARPlacementSystem.js';

export class ARCharacterView {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      enableMarkerTracking: options.enableMarkerTracking || false,
      enablePlaneDetection: options.enablePlaneDetection !== false,
      enableLightEstimation: options.enableLightEstimation !== false,
      enableOcclusion: options.enableOcclusion !== false,
      maxPlacedObjects: options.maxPlacedObjects || 20,
      placementDistance: options.placementDistance || 2,
      ...options
    };

    // Core systems
    this.arvrCore = null;
    this.cameraController = null;
    this.placementSystem = null;

    // AR Components
    this.characterSheet = null;
    this.diceRoller = null;
    this.spellEffects = null;
    this.monsterViewer = null;

    // AR state
    this.isARSessionActive = false;
    this.detectedPlanes = new Map();
    this.placedObjects = new Map();
    this.isPlacingObject = false;
    this.currentPlacementType = null;
    this.reticle = null;

    // Device capabilities
    this.deviceCapabilities = {
      hasAR: false,
      hasPlaneDetection: false,
      hasLightEstimation: false,
      hasOcclusion: false,
      hasFaceTracking: false,
      isIOS: false,
      isAndroid: false
    };

    // Performance optimization
    this.performanceMode = 'balanced'; // 'performance', 'balanced', 'quality'
    this.adaptiveQuality = true;

    this.eventListeners = new Map();
  }

  async initialize() {
    try {
      this.showLoadingScreen('Initializing AR Character View...');

      // Detect device capabilities
      await this.detectARCapabilities();

      // Initialize core AR system
      await this.initializeARCore();

      // Initialize camera controller
      await this.initializeCameraController();

      // Initialize placement system
      await this.initializePlacementSystem();

      // Initialize AR components
      await this.initializeARComponents();

      // Setup AR session
      await this.setupARSession();

      // Start render loop
      this.startRenderLoop();

      this.isARSessionActive = true;
      this.hideLoadingScreen();

      this.emit('arInitialized', this.deviceCapabilities);
      console.log('AR Character View initialized successfully');

      return true;
    } catch (error) {
      console.error('Failed to initialize AR Character View:', error);
      this.hideLoadingScreen();
      this.emit('arError', error);
      return false;
    }
  }

  async detectARCapabilities() {
    // Check WebXR support
    if ('xr' in navigator) {
      try {
        this.deviceCapabilities.hasAR = await navigator.xr.isSessionSupported('immersive-ar');
      } catch (error) {
        console.warn('AR support detection failed:', error);
      }
    }

    // Detect device type
    const userAgent = navigator.userAgent.toLowerCase();
    this.deviceCapabilities.isIOS = /iphone|ipad|ipod/.test(userAgent);
    this.deviceCapabilities.isAndroid = /android/.test(userAgent);

    // Check for specific AR features
    if (this.deviceCapabilities.isIOS) {
      this.deviceCapabilities.hasFaceTracking = true; // ARKit face tracking
      this.deviceCapabilities.hasLightEstimation = true; // ARKit light estimation
      this.deviceCapabilities.hasOcclusion = true; // ARKit people occlusion
    } else if (this.deviceCapabilities.isAndroid) {
      this.deviceCapabilities.hasPlaneDetection = true; // ARCore plane detection
      this.deviceCapabilities.hasLightEstimation = true; // ARCore light estimation
    }

    console.log('AR Device Capabilities:', this.deviceCapabilities);
  }

  async initializeARCore() {
    this.arvrCore = new ARVRCore({
      container: this.container,
      enableVR: false,
      enableAR: true,
      alpha: true,
      antialias: true,
      preserveDrawingBuffer: true
    });

    await this.arvrCore.initialize();
    this.setupCoreEventHandlers();
  }

  async initializeCameraController() {
    this.cameraController = new ARCameraController(this.arvrCore, {
      enableTapToPlace: true,
      enablePinchToScale: true,
      enableDragToRotate: true,
      movementSpeed: 0.1,
      rotationSpeed: 0.01
    });

    await this.cameraController.initialize();
    this.setupCameraEventHandlers();
  }

  async initializePlacementSystem() {
    this.placementSystem = new ARPlacementSystem(this.arvrCore, {
      enablePlaneDetection: this.options.enablePlaneDetection,
      enableHitTesting: true,
      placementDistance: this.options.placementDistance,
      maxObjects: this.options.maxPlacedObjects
    });

    await this.placementSystem.initialize();
    this.setupPlacementEventHandlers();
  }

  async initializeARComponents() {
    // Initialize Character Sheet
    this.characterSheet = new ARCharacterSheet(this.arvrCore, {
      enable3DAvatar: true,
      enableStats: true,
      enableEquipment: true,
      position: new THREE.Vector3(-1, 1, -2)
    });

    // Initialize Dice Roller
    this.diceRoller = new ARDiceRoller(this.arvrCore, {
      enablePhysics: true,
      enableSounds: true,
      diceSize: 0.1,
      position: new THREE.Vector3(0, 0.5, -1.5)
    });

    // Initialize Spell Effects
    this.spellEffects = new ARSpellEffects(this.arvrCore, {
      enableParticles: true,
      enableSounds: true,
      enablePhysics: true,
      maxEffects: 10
    });

    // Initialize Monster Viewer
    this.monsterViewer = new ARMonsterViewer(this.arvrCore, {
      enable3DModels: true,
      enableAnimations: true,
      enableInfo: true,
      position: new THREE.Vector3(1, 1, -2)
    });

    // Initialize all components
    await Promise.all([
      this.characterSheet.initialize(),
      this.diceRoller.initialize(),
      this.spellEffects.initialize(),
      this.monsterViewer.initialize()
    ]);

    this.setupComponentEventHandlers();
  }

  async setupARSession() {
    if (!this.deviceCapabilities.hasAR) {
      throw new Error('AR not supported on this device');
    }

    try {
      const session = await navigator.xr.requestSession('immersive-ar', {
        requiredFeatures: ['local', 'hit-test'],
        optionalFeatures: [
          'plane-detection',
          'light-estimation',
          'dominant-hand',
          'anchors'
        ]
      });

      await this.arvrCore.renderer.xr.setSession(session);
      this.setupSessionEventHandlers(session);

      // Setup reticle for placement
      this.createPlacementReticle();

      // Start plane detection if available
      if (this.options.enablePlaneDetection) {
        this.startPlaneDetection(session);
      }

      // Setup light estimation if available
      if (this.options.enableLightEstimation) {
        this.setupLightEstimation(session);
      }

    } catch (error) {
      console.error('Failed to setup AR session:', error);
      throw error;
    }
  }

  createPlacementReticle() {
    const geometry = new THREE.RingGeometry(0.1, 0.15, 32);
    const material = new THREE.MeshBasicMaterial({
      color: 0x4ecdc4,
      transparent: true,
      opacity: 0.7
    });

    this.reticle = new THREE.Mesh(geometry, material);
    this.reticle.rotation.x = -Math.PI / 2;
    this.reticle.visible = false;
    this.arvrCore.scene.add(this.reticle);
  }

  startPlaneDetection(session) {
    // Detect horizontal planes for placement
    session.requestReferenceSpace('viewer').then((referenceSpace) => {
      session.requestAnimationFrame((frame, time) => {
        if (!this.isARSessionActive) return;

        // Get hit test results
        const hitTestResults = frame.getHitTestResultsForTransientInput(session.inputSources[0]);

        if (hitTestResults.length > 0) {
          const hitPose = hitTestResults[0].getPose(referenceSpace);
          if (hitPose) {
            // Update reticle position
            this.reticle.position.setFromMatrixPosition(hitPose.transform.matrix);
            this.reticle.visible = this.isPlacingObject;
          }
        }

        session.requestAnimationFrame(this.startPlaneDetection.bind(this, session));
      });
    });
  }

  setupLightEstimation(session) {
    session.requestLightEstimate().then((lightEstimate) => {
      if (lightEstimate) {
        // Adjust scene lighting based on real-world lighting
        this.updateSceneLighting(lightEstimate);
      }
    });
  }

  updateSceneLighting(lightEstimate) {
    // Update ambient light intensity
    if (this.arvrCore.lights && this.arvrCore.lights.ambient) {
      const ambientIntensity = lightEstimate.ambientIntensity || 1.0;
      this.arvrCore.lights.ambient.intensity = ambientIntensity * 0.5;
    }

    // Update main light color based on real world
    if (this.arvrCore.lights && this.arvrCore.lights.directional) {
      const lightColor = lightEstimate.primaryLightColor || { r: 1, g: 1, b: 1 };
      this.arvrCore.lights.directional.color.setRGB(
        lightColor.r,
        lightColor.g,
        lightColor.b
      );
    }
  }

  setupCoreEventHandlers() {
    this.arvrCore.on('sessionStart', (data) => {
      if (data.isAR) {
        this.onARSessionStart();
      }
    });

    this.arvrCore.on('sessionEnd', () => {
      this.onARSessionEnd();
    });

    this.arvrCore.on('objectSelected', (data) => {
      this.handleObjectSelection(data);
    });
  }

  setupCameraEventHandlers() {
    this.cameraController.on('tap', (position) => {
      this.handleTap(position);
    });

    this.cameraController.on('pinch', (scale) => {
      this.handlePinch(scale);
    });

    this.cameraController.on('drag', (delta) => {
      this.handleDrag(delta);
    });
  }

  setupPlacementEventHandlers() {
    this.placementSystem.on('planeDetected', (plane) => {
      this.detectedPlanes.set(plane.id, plane);
      this.emit('planeDetected', plane);
    });

    this.placementSystem.on('hitTest', (result) => {
      this.updateReticlePosition(result);
    });

    this.placementSystem.on('objectPlaced', (object) => {
      this.placedObjects.set(object.id, object);
      this.emit('objectPlaced', object);
    });
  }

  setupComponentEventHandlers() {
    this.characterSheet.on('statChanged', (data) => {
      this.emit('characterStatChanged', data);
    });

    this.diceRoller.on('diceRolled', (data) => {
      this.emit('diceRolled', data);
    });

    this.spellEffects.on('spellEffectStarted', (data) => {
      this.emit('spellEffectStarted', data);
    });

    this.monsterViewer.on('monsterSelected', (data) => {
      this.emit('monsterSelected', data);
    });
  }

  setupSessionEventHandlers(session) {
    session.addEventListener('end', () => {
      this.onARSessionEnd();
    });

    session.addEventListener('visibilitychange', (event) => {
      this.handleVisibilityChange(event);
    });
  }

  onARSessionStart() {
    console.log('AR Session started');
    this.emit('arSessionStart');

    // Show AR instructions
    this.showARInstructions();
  }

  onARSessionEnd() {
    console.log('AR Session ended');
    this.isARSessionActive = false;
    this.emit('arSessionEnd');

    // Clean up placed objects
    this.cleanupPlacedObjects();
  }

  showARInstructions() {
    // Show temporary UI overlay with AR instructions
    const instructions = document.createElement('div');
    instructions.id = 'ar-instructions';
    instructions.innerHTML = `
      <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                  background: rgba(0,0,0,0.8); color: white; padding: 20px;
                  border-radius: 10px; text-align: center; z-index: 10000;">
        <h3>AR Controls</h3>
        <p>👆 Tap to place objects</p>
        <p>🤏 Pinch to scale objects</p>
        <p>✋ Drag to rotate objects</p>
        <p>🎯 Point camera at surfaces to detect</p>
        <button onclick="this.parentElement.parentElement.remove()"
                style="margin-top: 10px; padding: 10px 20px; background: #4ecdc4;
                       border: none; border-radius: 5px; color: white; cursor: pointer;">
          Got it!
        </button>
      </div>
    `;
    document.body.appendChild(instructions);

    // Auto-hide after 5 seconds
    setTimeout(() => {
      const element = document.getElementById('ar-instructions');
      if (element) element.remove();
    }, 5000);
  }

  handleTap(screenPosition) {
    if (this.isPlacingObject && this.reticle.visible) {
      this.placeCurrentObject();
    } else {
      // Check if tapping on existing object
      this.checkObjectTap(screenPosition);
    }
  }

  handlePinch(scale) {
    // Scale selected object
    if (this.selectedObject) {
      this.selectedObject.scale.multiplyScalar(scale);
      this.emit('objectScaled', { object: this.selectedObject, scale });
    }
  }

  handleDrag(delta) {
    // Rotate selected object
    if (this.selectedObject) {
      this.selectedObject.rotation.y += delta.x * 0.01;
      this.emit('objectRotated', { object: this.selectedObject, rotation: this.selectedObject.rotation });
    }
  }

  handleObjectSelection(data) {
    this.selectedObject = data.object;
    this.emit('objectSelected', data);
  }

  checkObjectTap(screenPosition) {
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2(
      (screenPosition.x / window.innerWidth) * 2 - 1,
      -(screenPosition.y / window.innerHeight) * 2 + 1
    );

    raycaster.setFromCamera(mouse, this.arvrCore.camera);
    const intersects = raycaster.intersectObjects(this.arvrCore.scene.children, true);

    if (intersects.length > 0) {
      const object = intersects[0].object;
      this.handleObjectSelection({ object, intersection: intersects[0] });
    }
  }

  updateReticlePosition(hitResult) {
    if (this.reticle && hitResult) {
      this.reticle.position.setFromMatrixPosition(hitResult.transform.matrix);
      this.reticle.visible = this.isPlacingObject;
    }
  }

  // Public API methods
  startPlacement(objectType, options = {}) {
    this.isPlacingObject = true;
    this.currentPlacementType = objectType;
    this.placementOptions = options;

    if (this.reticle) {
      this.reticle.visible = true;
    }

    this.emit('placementStarted', { type: objectType, options });
  }

  placeCurrentObject() {
    if (!this.currentPlacementType || !this.reticle.visible) return;

    let object = null;

    switch (this.currentPlacementType) {
      case 'character-sheet':
        object = this.characterSheet.createARSheet(this.reticle.position.clone());
        break;
      case 'dice':
        object = this.diceRoller.placeDiceSet(this.reticle.position.clone());
        break;
      case 'monster':
        object = this.monsterViewer.spawnMonster(
          this.placementOptions.monsterType || 'goblin',
          this.reticle.position.clone()
        );
        break;
      case 'spell-effect':
        object = this.spellEffects.createSpellEffect(
          this.placementOptions.spellType || 'fireball',
          this.reticle.position.clone()
        );
        break;
    }

    if (object) {
      this.placedObjects.set(object.id, object);
      this.emit('objectPlaced', { type: this.currentPlacementType, object });
    }

    this.stopPlacement();
  }

  stopPlacement() {
    this.isPlacingObject = false;
    this.currentPlacementType = null;
    this.placementOptions = null;

    if (this.reticle) {
      this.reticle.visible = false;
    }

    this.emit('placementStopped');
  }

  placeCharacterSheet(position) {
    return this.characterSheet.placeInAR(position);
  }

  placeDice(position) {
    return this.diceRoller.placeDice(position);
  }

  placeMonster(monsterType, position) {
    return this.monsterViewer.placeMonster(monsterType, position);
  }

  castSpellInAR(spellType, position) {
    return this.spellEffects.castSpell(spellType, position);
  }

  rollVirtualDice(diceType, result) {
    return this.diceRoller.rollDiceInAR(diceType, result);
  }

  showMonsterInAR(monsterData, position) {
    return this.monsterViewer.showMonster(monsterData, position);
  }

  updateCharacterData(characterData) {
    return this.characterSheet.updateData(characterData);
  }

  handleVisibilityChange(event) {
    const isVisible = event.session.visibilityState === 'visible';
    if (!isVisible) {
      // Pause rendering when not visible
      this.pause();
    } else {
      // Resume when visible again
      this.resume();
    }
  }

  pause() {
    this.isPaused = true;
    this.emit('paused');
  }

  resume() {
    this.isPaused = false;
    this.emit('resumed');
  }

  cleanupPlacedObjects() {
    for (const object of this.placedObjects.values()) {
      this.arvrCore.scene.remove(object);
    }
    this.placedObjects.clear();
  }

  // Performance optimization
  setPerformanceMode(mode) {
    this.performanceMode = mode;
    this.applyPerformanceSettings();
  }

  applyPerformanceSettings() {
    switch (this.performanceMode) {
      case 'performance':
        this.arvrCore.renderer.setPixelRatio(1);
        this.arvrCore.renderer.shadowMap.enabled = false;
        break;
      case 'balanced':
        this.arvrCore.renderer.setPixelRatio(Math.min(1.5, window.devicePixelRatio));
        this.arvrCore.renderer.shadowMap.enabled = true;
        break;
      case 'quality':
        this.arvrCore.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
        this.arvrCore.renderer.shadowMap.enabled = true;
        break;
    }
  }

  // Render loop
  startRenderLoop() {
    const animate = () => {
      if (!this.isARSessionActive || this.isPaused) return;

      const delta = this.arvrCore.clock.getDelta();

      // Update components
      if (this.characterSheet) {
        this.characterSheet.update(delta);
      }

      if (this.diceRoller) {
        this.diceRoller.update(delta);
      }

      if (this.spellEffects) {
        this.spellEffects.update(delta);
      }

      if (this.monsterViewer) {
        this.monsterViewer.update(delta);
      }

      // Update camera controller
      if (this.cameraController) {
        this.cameraController.update(delta);
      }

      // Update placement system
      if (this.placementSystem) {
        this.placementSystem.update(delta);
      }

      // Adaptive quality management
      if (this.adaptiveQuality) {
        this.updateAdaptiveQuality();
      }

      requestAnimationFrame(animate);
    };

    animate();
  }

  updateAdaptiveQuality() {
    const fps = this.arvrCore.performanceMonitor.fps;

    if (fps < 30) {
      this.setPerformanceMode('performance');
    } else if (fps < 50) {
      this.setPerformanceMode('balanced');
    } else {
      this.setPerformanceMode('quality');
    }
  }

  showLoadingScreen(text = 'Loading...') {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      const loadingText = loadingScreen.querySelector('.loading-text');
      if (loadingText) loadingText.textContent = text;
      loadingScreen.classList.remove('hidden');
    }
  }

  hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
      loadingScreen.style.opacity = '0';
      setTimeout(() => {
        loadingScreen.classList.add('hidden');
        loadingScreen.style.opacity = '1';
      }, 500);
    }
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
    this.isARSessionActive = false;

    // Cleanup components
    if (this.characterSheet) {
      this.characterSheet.dispose();
    }

    if (this.diceRoller) {
      this.diceRoller.dispose();
    }

    if (this.spellEffects) {
      this.spellEffects.dispose();
    }

    if (this.monsterViewer) {
      this.monsterViewer.dispose();
    }

    // Cleanup systems
    if (this.cameraController) {
      this.cameraController.dispose();
    }

    if (this.placementSystem) {
      this.placementSystem.dispose();
    }

    // Cleanup placed objects
    this.cleanupPlacedObjects();

    // Cleanup reticle
    if (this.reticle) {
      this.arvrCore.scene.remove(this.reticle);
    }

    // Cleanup core
    if (this.arvrCore) {
      this.arvrCore.dispose();
    }

    // Clear state
    this.detectedPlanes.clear();
    this.placedObjects.clear();
    this.eventListeners.clear();
  }
}

export default ARCharacterView;