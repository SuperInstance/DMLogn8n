/**
 * VR D&D Tabletop Experience
 * Provides immersive virtual tabletop with 3D miniatures, physics, and spell casting
 */

import * as THREE from 'three';
import { ARVRCore } from '../../core/ARVRCore.js';
import { TabletopEnvironment } from './environments/TabletopEnvironment.js';
import { MiniatureManager } from './components/MiniatureManager.js';
import { DiceRoller } from './components/DiceRoller.js';
import { SpellCastingSystem } from './components/SpellCastingSystem.js';
import { PhysicsEngine } from './physics/PhysicsEngine.js';
import { AudioManager } from './audio/AudioManager.js';
import { HandGestureRecognition } from './input/HandGestureRecognition.js';
import { VoiceChatSystem } from './communication/VoiceChatSystem.js';

export class VRTabletop {
  constructor(container, options = {}) {
    this.container = container;
    this.options = {
      enablePhysics: options.enablePhysics !== false,
      enableSpatialAudio: options.enableSpatialAudio !== false,
      enableHandTracking: options.enableHandTracking !== false,
      enableVoiceChat: options.enableVoiceChat !== false,
      maxPlayers: options.maxPlayers || 6,
      tabletopSize: options.tabletopSize || { width: 8, height: 8 },
      ...options
    };

    // Core systems
    this.arvrCore = null;
    this.physics = null;
    this.audio = null;
    this.gestureRecognition = null;
    this.voiceChat = null;

    // Game components
    this.environment = null;
    this.miniatureManager = null;
    this.diceRoller = null;
    this.spellCasting = null;

    // State management
    this.isInitialized = false;
    this.isTabletopReady = false;
    this.activePlayers = new Map();
    this.currentScene = null;

    // Performance tracking
    this.performanceMetrics = {
      fps: 0,
      frameTime: 0,
      memoryUsage: 0,
      networkLatency: 0
    };

    // Event system
    this.eventListeners = new Map();
  }

  async initialize() {
    try {
      this.showLoadingScreen('Initializing VR Tabletop...');

      // Initialize core AR/VR system
      this.arvrCore = new ARVRCore({
        container: this.container,
        enableVR: true,
        enableAR: true,
        enableHandTracking: this.options.enableHandTracking,
        targetFPS: 90,
        antialias: true
      });

      await this.arvrCore.initialize();
      this.setupCoreEventHandlers();

      // Initialize physics engine
      if (this.options.enablePhysics) {
        this.physics = new PhysicsEngine({
          gravity: { x: 0, y: -9.82, z: 0 },
          maxSteps: 4
        });
        await this.physics.initialize();
      }

      // Initialize audio system
      if (this.options.enableSpatialAudio) {
        this.audio = new AudioManager({
          spatialAudio: true,
          maxConcurrentSounds: 32,
          reverbPreset: 'dungeon'
        });
        await this.audio.initialize();
      }

      // Initialize gesture recognition
      if (this.options.enableHandTracking) {
        this.gestureRecognition = new HandGestureRecognition();
        await this.gestureRecognition.initialize();
      }

      // Initialize voice chat
      if (this.options.enableVoiceChat) {
        this.voiceChat = new VoiceChatSystem({
          maxPlayers: this.options.maxPlayers,
          spatialAudio: this.options.enableSpatialAudio
        });
        await this.voiceChat.initialize();
      }

      // Initialize game components
      await this.initializeEnvironment();
      await this.initializeMiniatures();
      await this.initializeDice();
      await thisinitializeSpellCasting();

      this.isInitialized = true;
      this.hideLoadingScreen();
      this.startRenderLoop();

      this.emit('initialized');
      console.log('VR Tabletop initialized successfully');

      return true;
    } catch (error) {
      console.error('Failed to initialize VR Tabletop:', error);
      this.hideLoadingScreen();
      this.emit('error', error);
      return false;
    }
  }

  async initializeEnvironment() {
    this.showLoadingScreen('Creating tabletop environment...');

    this.environment = new TabletopEnvironment(this.arvrCore, {
      size: this.options.tabletopSize,
      theme: 'dungeon',
      enableDynamicLighting: true,
      enableAtmosphericEffects: true
    });

    await this.environment.create();
    this.setupEnvironmentEventHandlers();

    this.showLoadingScreen('Loading dungeon tiles...');
    await this.environment.loadDungeonTiles();

    this.showLoadingScreen('Setting up lighting...');
    await this.environment.setupAdvancedLighting();

    this.isTabletopReady = true;
    this.emit('environmentReady');
  }

  async initializeMiniatures() {
    this.showLoadingScreen('Loading 3D miniatures...');

    this.miniatureManager = new MiniatureManager(this.arvrCore, {
      physics: this.physics,
      maxMiniatures: 50,
      enableCustomization: true
    });

    await this.miniatureManager.initialize();
    await this.miniatureManager.loadDefaultMiniatures();
    this.setupMiniatureEventHandlers();

    this.emit('miniaturesReady');
  }

  async initializeDice() {
    this.showLoadingScreen('Preparing dice system...');

    this.diceRoller = new DiceRoller(this.arvrCore, {
      physics: this.physics,
      audio: this.audio,
      spatialAudio: true
    });

    await this.diceRoller.initialize();
    this.setupDiceEventHandlers();

    this.emit('diceReady');
  }

  async initializeSpellCasting() {
    this.showLoadingScreen('Loading spell system...');

    this.spellCasting = new SpellCastingSystem(this.arvrCore, {
      gestureRecognition: this.gestureRecognition,
      audio: this.audio,
      physics: this.physics
    });

    await this.spellCasting.initialize();
    await this.spellCasting.loadSpellLibrary();
    this.setupSpellEventHandlers();

    this.emit('spellsReady');
  }

  setupCoreEventHandlers() {
    this.arvrCore.on('sessionStart', (data) => {
      this.emit('sessionStart', data);
      if (data.isVR) {
        this.setupVRSpecificFeatures();
      } else if (data.isAR) {
        this.setupARSpecificFeatures();
      }
    });

    this.arvrCore.on('sessionEnd', () => {
      this.emit('sessionEnd');
    });

    this.arvrCore.on('performanceUpdate', (metrics) => {
      this.updatePerformanceMetrics(metrics);
    });
  }

  setupEnvironmentEventHandlers() {
    this.environment.on('tilePlaced', (data) => {
      this.emit('tilePlaced', data);
    });

    this.environment.on('lightingChanged', (data) => {
      this.emit('lightingChanged', data);
    });

    this.environment.on('atmosphereChanged', (data) => {
      this.emit('atmosphereChanged', data);
    });
  }

  setupMiniatureEventHandlers() {
    this.miniatureManager.on('miniaturePlaced', (data) => {
      this.emit('miniaturePlaced', data);
    });

    this.miniatureManager.on('miniatureMoved', (data) => {
      this.emit('miniatureMoved', data);
    });

    this.miniatureManager.on('miniatureSelected', (data) => {
      this.emit('miniatureSelected', data);
    });
  }

  setupDiceEventHandlers() {
    this.diceRoller.on('diceRolled', (data) => {
      this.emit('diceRolled', data);
    });

    this.diceRoller.on('diceSettled', (data) => {
      this.emit('diceSettled', data);
    });
  }

  setupSpellEventHandlers() {
    this.spellCasting.on('spellCast', (data) => {
      this.emit('spellCast', data);
    });

    this.spellCasting.on('spellEffect', (data) => {
      this.emit('spellEffect', data);
    });
  }

  setupVRSpecificFeatures() {
    // VR-specific optimizations and features
    this.container.classList.add('vr-mode');

    // Adjust UI for VR
    this.adjustUIForVR();

    // Enable hand gestures
    if (this.gestureRecognition) {
      this.gestureRecognition.enableGestureRecognition();
    }

    // Setup comfort features
    this.setupComfortFeatures();
  }

  setupARSpecificFeatures() {
    // AR-specific features
    this.container.classList.add('ar-mode');

    // Enable real-world interaction
    this.enableRealWorldInteraction();

    // Setup AR-specific UI
    this.adjustUIForAR();
  }

  adjustUIForVR() {
    const panels = document.querySelectorAll('.ui-panel');
    panels.forEach(panel => {
      panel.style.transform = 'scale(0.8)';
      panel.style.opacity = '0.9';
    });
  }

  adjustUIForAR() {
    const panels = document.querySelectorAll('.ui-panel');
    panels.forEach(panel => {
      panel.style.background = 'rgba(0, 0, 0, 0.7)';
      panel.style.backdropFilter = 'blur(5px)';
    });
  }

  setupComfortFeatures() {
    // Enable snap turning for comfort
    this.arvrCore.enableSnapTurning = true;

    // Set comfortable movement speed
    this.arvrCore.movementSpeed = 3.0;

    // Enable vignette for motion sickness prevention
    this.arvrCore.enableVignette = true;
  }

  enableRealWorldInteraction() {
    // Enable collision with real-world surfaces
    if (this.physics) {
      this.physics.enableRealWorldCollisions = true;
    }
  }

  // Scene management
  async loadScene(sceneData) {
    this.showLoadingScreen('Loading game scene...');

    try {
      // Clear current scene
      await this.clearScene();

      // Load new scene data
      this.currentScene = sceneData;

      // Load terrain
      if (sceneData.terrain) {
        await this.environment.loadTerrain(sceneData.terrain);
      }

      // Place miniatures
      if (sceneData.miniatures) {
        await this.miniatureManager.placeMiniatures(sceneData.miniatures);
      }

      // Setup lighting
      if (sceneData.lighting) {
        await this.environment.applyLightingPreset(sceneData.lighting);
      }

      // Apply atmosphere
      if (sceneData.atmosphere) {
        await this.environment.setAtmosphere(sceneData.atmosphere);
      }

      this.emit('sceneLoaded', sceneData);
      this.hideLoadingScreen();

      return true;
    } catch (error) {
      console.error('Failed to load scene:', error);
      this.hideLoadingScreen();
      return false;
    }
  }

  async clearScene() {
    await this.miniatureManager.removeAllMiniatures();
    await this.environment.clear();
    this.currentScene = null;
  }

  // Player management
  addPlayer(playerData) {
    if (this.activePlayers.size >= this.options.maxPlayers) {
      throw new Error('Maximum number of players reached');
    }

    const player = {
      id: playerData.id,
      name: playerData.name,
      color: playerData.color || this.generatePlayerColor(),
      miniature: null,
      position: playerData.position || { x: 0, y: 0, z: 0 },
      isActive: true,
      joinedAt: Date.now()
    };

    this.activePlayers.set(player.id, player);

    // Create player miniature
    this.miniatureManager.createPlayerMiniature(player);

    // Connect voice chat
    if (this.voiceChat) {
      this.voiceChat.addPlayer(player);
    }

    this.emit('playerJoined', player);
    return player;
  }

  removePlayer(playerId) {
    const player = this.activePlayers.get(playerId);
    if (!player) return false;

    // Remove miniature
    if (player.miniature) {
      this.miniatureManager.removeMiniature(player.miniature);
    }

    // Disconnect voice chat
    if (this.voiceChat) {
      this.voiceChat.removePlayer(playerId);
    }

    this.activePlayers.delete(playerId);
    this.emit('playerLeft', player);
    return true;
  }

  generatePlayerColor() {
    const colors = [0xff6b6b, 0x4ecdc4, 0x45b7d1, 0xf9ca24, 0xf0932b, 0xeb4d4b];
    return colors[Math.floor(Math.random() * colors.length)];
  }

  // Game actions
  placeDungeonTile(tileData, position) {
    return this.environment.placeTile(tileData, position);
  }

  moveMiniature(miniatureId, position) {
    return this.miniatureManager.moveMiniature(miniatureId, position);
  }

  rollDice(diceType, count = 1) {
    return this.diceRoller.roll(diceType, count);
  }

  castSpell(spellId, target, options = {}) {
    return this.spellCasting.cast(spellId, target, options);
  }

  // Performance monitoring
  updatePerformanceMetrics(metrics) {
    this.performanceMetrics = { ...this.performanceMetrics, ...metrics };

    // Update UI if available
    const fpsElement = document.getElementById('fps-counter');
    const memoryElement = document.getElementById('memory-usage');

    if (fpsElement) {
      fpsElement.textContent = metrics.fps;
    }

    if (memoryElement && metrics.memoryUsage) {
      memoryElement.textContent = `${Math.round(metrics.memoryUsage)}MB`;
    }

    // Adaptive quality management
    this.manageAdaptiveQuality(metrics);
  }

  manageAdaptiveQuality(metrics) {
    const targetFPS = 90;
    const currentFPS = metrics.fps;

    if (currentFPS < targetFPS * 0.8) {
      // Reduce quality
      this.reduceQuality();
    } else if (currentFPS > targetFPS * 0.95) {
      // Increase quality
      this.increaseQuality();
    }
  }

  reduceQuality() {
    if (this.arvrCore.renderer) {
      this.arvrCore.renderer.setPixelRatio(Math.max(0.5, this.arvrCore.renderer.getPixelRatio() * 0.9));
    }
  }

  increaseQuality() {
    if (this.arvrCore.renderer) {
      const maxPixelRatio = Math.min(2, window.devicePixelRatio);
      this.arvrCore.renderer.setPixelRatio(Math.min(maxPixelRatio, this.arvrCore.renderer.getPixelRatio() * 1.1));
    }
  }

  // UI helpers
  showLoadingScreen(text = 'Loading...') {
    const loadingScreen = document.getElementById('loading-screen');
    const loadingText = loadingScreen.querySelector('.loading-text');
    const progressBar = document.getElementById('progress-bar');

    if (loadingText) loadingText.textContent = text;
    if (progressBar) progressBar.style.width = '0%';
    loadingScreen.classList.remove('hidden');
  }

  updateLoadingProgress(progress) {
    const progressBar = document.getElementById('progress-bar');
    if (progressBar) {
      progressBar.style.width = `${Math.min(100, progress)}%`;
    }
  }

  hideLoadingScreen() {
    const loadingScreen = document.getElementById('loading-screen');
    loadingScreen.style.opacity = '0';
    setTimeout(() => {
      loadingScreen.classList.add('hidden');
      loadingScreen.style.opacity = '1';
    }, 500);
  }

  // Render loop
  startRenderLoop() {
    const animate = () => {
      if (!this.isInitialized) return;

      const delta = this.arvrCore.clock.getDelta();

      // Update physics
      if (this.physics) {
        this.physics.step(delta);
      }

      // Update audio
      if (this.audio) {
        this.audio.update(delta);
      }

      // Update gesture recognition
      if (this.gestureRecognition) {
        this.gestureRecognition.update(delta);
      }

      // Update components
      if (this.environment) {
        this.environment.update(delta);
      }

      if (this.miniatureManager) {
        this.miniatureManager.update(delta);
      }

      if (this.diceRoller) {
        this.diceRoller.update(delta);
      }

      if (this.spellCasting) {
        this.spellCasting.update(delta);
      }

      requestAnimationFrame(animate);
    };

    animate();
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
    // Stop render loop
    this.isInitialized = false;

    // Dispose components
    if (this.environment) {
      this.environment.dispose();
    }

    if (this.miniatureManager) {
      this.miniatureManager.dispose();
    }

    if (this.diceRoller) {
      this.diceRoller.dispose();
    }

    if (this.spellCasting) {
      this.spellCasting.dispose();
    }

    // Dispose systems
    if (this.physics) {
      this.physics.dispose();
    }

    if (this.audio) {
      this.audio.dispose();
    }

    if (this.voiceChat) {
      this.voiceChat.dispose();
    }

    if (this.gestureRecognition) {
      this.gestureRecognition.dispose();
    }

    // Dispose core
    if (this.arvrCore) {
      this.arvrCore.dispose();
    }

    // Clear state
    this.activePlayers.clear();
    this.eventListeners.clear();
  }
}

export default VRTabletop;