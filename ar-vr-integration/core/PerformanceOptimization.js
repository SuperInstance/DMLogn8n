/**
 * Performance Optimization and Comfort Settings for AR/VR D&D
 * Handles 90 FPS target, adaptive quality, latency minimization, and motion sickness prevention
 */

import * as THREE from 'three';

export class PerformanceOptimization {
  constructor(arvrCore, options = {}) {
    this.arvrCore = arvrCore;
    this.options = {
      targetFPS: options.targetFPS || 90,
      enableAdaptiveQuality: options.enableAdaptiveQuality !== false,
      enableComfortSettings: options.enableComfortSettings !== false,
      enableMotionSicknessPrevention: options.enableMotionSicknessPrevention !== false,
      enableLatencyOptimization: options.enableLatencyOptimization !== false,
      enableAssetStreaming: options.enableAssetStreaming !== false,
      maxRenderTime: options.maxRenderTime || 11.11, // 90 FPS = 11.11ms per frame
      adaptiveQualityThreshold: options.adaptiveQualityThreshold || 10,
      ...options
    };

    // Performance monitoring
    this.performanceMetrics = {
      fps: 0,
      frameTime: 0,
      frameCount: 0,
      lastFrameTime: performance.now(),
      frameTimes: [],
      averageFrameTime: 0,
      worstFrameTime: 0,
      memoryUsage: 0,
      drawCalls: 0,
      triangles: 0,
      textureMemory: 0,
      networkLatency: 0
    };

    // Quality settings
    this.qualityLevels = {
      ultra: {
        pixelRatio: 2.0,
        shadowMapSize: 2048,
        antialias: true,
        textureQuality: 'high',
        lodBias: 0,
        renderScale: 1.0
      },
      high: {
        pixelRatio: 1.5,
        shadowMapSize: 1024,
        antialias: true,
        textureQuality: 'high',
        lodBias: -0.5,
        renderScale: 1.0
      },
      medium: {
        pixelRatio: 1.0,
        shadowMapSize: 512,
        antialias: true,
        textureQuality: 'medium',
        lodBias: -1.0,
        renderScale: 0.8
      },
      low: {
        pixelRatio: 0.8,
        shadowMapSize: 256,
        antialias: false,
        textureQuality: 'low',
        lodBias: -2.0,
        renderScale: 0.6
      },
      potato: {
        pixelRatio: 0.5,
        shadowMapSize: 128,
        antialias: false,
        textureQuality: 'low',
        lodBias: -3.0,
        renderScale: 0.4
      }
    };

    this.currentQualityLevel = 'high';
    this.adaptiveQualityEnabled = this.options.enableAdaptiveQuality;

    // Comfort settings
    this.comfortSettings = {
      snapTurning: true,
      vignetteStrength: 0.0,
      movementSpeed: 1.0,
      rotationSpeed: 1.0,
     FOV: 90,
      comfortMode: 'normal', // 'normal', 'comfortable', 'maximum'
      smoothLocomotion: false,
      dynamicFOV: false,
      peripheralVignette: false
    };

    // Motion sickness prevention
    this.motionSicknessSettings = {
      enableVignette: false,
      vignetteRadius: 0.8,
      enableMotionPrediction: true,
      predictionAmount: 0.1,
      enableStabilization: true,
      stabilizationStrength: 0.5,
      enableBreathingGuidance: false,
      breathingPattern: '4-7-8'
    };

    // Asset streaming
    this.assetStreamingManager = null;
    this.assetCache = new Map();
    this.loadingAssets = new Set();

    // Optimization systems
    this.lodManager = new LODManager();
    this.cullingManager = new CullingManager();
    this.textureOptimizer = new TextureOptimizer();
    this.geometryOptimizer = new GeometryOptimizer();

    this.isInitialized = false;
    this.eventListeners = new Map();
  }

  async initialize() {
    try {
      console.log('Initializing Performance Optimization System...');

      // Initialize performance monitoring
      this.initializePerformanceMonitoring();

      // Initialize comfort settings
      if (this.options.enableComfortSettings) {
        this.initializeComfortSettings();
      }

      // Initialize motion sickness prevention
      if (this.options.enableMotionSicknessPrevention) {
        this.initializeMotionSicknessPrevention();
      }

      // Initialize asset streaming
      if (this.options.enableAssetStreaming) {
        await this.initializeAssetStreaming();
      }

      // Initialize optimization managers
      await this.initializeOptimizationManagers();

      // Apply initial quality settings
      this.applyQualitySettings(this.currentQualityLevel);

      // Start performance monitoring loop
      this.startPerformanceMonitoring();

      this.isInitialized = true;
      this.emit('performanceInitialized');

      console.log('Performance Optimization System initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize Performance Optimization System:', error);
      this.emit('performanceError', error);
      return false;
    }
  }

  initializePerformanceMonitoring() {
    // Setup performance observers
    if ('PerformanceObserver' in window) {
      this.frameTimeObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach(entry => {
          if (entry.entryType === 'measure') {
            this.updateFrameTimeMetrics(entry.duration);
          }
        });
      });

      this.frameTimeObserver.observe({ entryTypes: ['measure'] });
    }

    // Memory monitoring
    if (performance.memory) {
      setInterval(() => {
        this.performanceMetrics.memoryUsage = performance.memory.usedJSHeapSize / 1048576; // MB
      }, 1000);
    }
  }

  initializeComfortSettings() {
    // Detect VR/AR and apply appropriate comfort settings
    if (this.arvrCore.isVR) {
      this.comfortSettings.snapTurning = true;
      this.comfortSettings.smoothLocomotion = false;
      this.comfortSettings.dynamicFOV = true;
      this.comfortSettings.peripheralVignette = true;
    }

    // Setup comfort mode based on user preference or device
    this.setComfortMode(this.comfortSettings.comfortMode);
  }

  initializeMotionSicknessPrevention() {
    // Create vignette material for motion sickness prevention
    this.vignetteMaterial = new THREE.ShaderMaterial({
      uniforms: {
        strength: { value: 0.0 },
        radius: { value: 0.8 },
        smoothing: { value: 0.2 }
      },
      vertexShader: `
        varying vec2 vUv;
        void main() {
          vUv = uv;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform float strength;
        uniform float radius;
        uniform float smoothing;
        varying vec2 vUv;

        void main() {
          vec2 center = vec2(0.5, 0.5);
          float dist = distance(vUv, center);
          float vignette = 1.0 - smoothstep(radius - smoothing, radius + smoothing, dist);
          vignette = 1.0 - (1.0 - vignette) * strength;

          gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0 - vignette);
        }
      `,
      transparent: true,
      depthTest: false,
      depthWrite: false
    });

    // Create vignette mesh
    const vignetteGeometry = new THREE.PlaneGeometry(2, 2);
    this.vignetteMesh = new THREE.Mesh(vignetteGeometry, this.vignetteMaterial);
    this.vignetteMesh.renderOrder = 1000; // Render last

    console.log('Motion sickness prevention initialized');
  }

  async initializeAssetStreaming() {
    this.assetStreamingManager = new AssetStreamingManager({
      maxConcurrentLoads: 3,
      cacheSize: 100,
      compressionEnabled: true,
      lodEnabled: true
    });

    await this.assetStreamingManager.initialize();
    console.log('Asset streaming initialized');
  }

  async initializeOptimizationManagers() {
    await this.lodManager.initialize(this.arvrCore);
    await this.cullingManager.initialize(this.arvrCore);
    await this.textureOptimizer.initialize(this.arvrCore);
    await this.geometryOptimizer.initialize(this.arvrCore);

    console.log('Optimization managers initialized');
  }

  startPerformanceMonitoring() {
    let lastTime = performance.now();
    let frameCount = 0;

    const monitorFrame = () => {
      const currentTime = performance.now();
      const deltaTime = currentTime - lastTime;

      // Update frame time metrics
      this.updateFrameTimeMetrics(deltaTime);

      // Calculate FPS
      frameCount++;
      if (frameCount >= 30) { // Average over 30 frames
        this.performanceMetrics.fps = Math.round(1000 / (deltaTime / frameCount));
        frameCount = 0;

        // Trigger adaptive quality adjustment
        if (this.adaptiveQualityEnabled) {
          this.adjustAdaptiveQuality();
        }
      }

      lastTime = currentTime;

      // Continue monitoring
      requestAnimationFrame(monitorFrame);
    };

    monitorFrame();
  }

  updateFrameTimeMetrics(frameTime) {
    this.performanceMetrics.frameTime = frameTime;
    this.performanceMetrics.frameTimes.push(frameTime);

    // Keep only last 60 frame times
    if (this.performanceMetrics.frameTimes.length > 60) {
      this.performanceMetrics.frameTimes.shift();
    }

    // Calculate average frame time
    const sum = this.performanceMetrics.frameTimes.reduce((a, b) => a + b, 0);
    this.performanceMetrics.averageFrameTime = sum / this.performanceMetrics.frameTimes.length;

    // Track worst frame time
    if (frameTime > this.performanceMetrics.worstFrameTime) {
      this.performanceMetrics.worstFrameTime = frameTime;
    }

    // Update render statistics
    if (this.arvrCore.renderer) {
      this.performanceMetrics.drawCalls = this.arvrCore.renderer.info.render.calls;
      this.performanceMetrics.triangles = this.arvrCore.renderer.info.render.triangles;
    }

    // Emit performance update
    this.emit('performanceUpdate', this.performanceMetrics);
  }

  adjustAdaptiveQuality() {
    const averageFrameTime = this.performanceMetrics.averageFrameTime;
    const targetFrameTime = 1000 / this.options.targetFPS;
    const threshold = this.options.adaptiveQualityThreshold;

    if (averageFrameTime > targetFrameTime + threshold) {
      // Performance is poor, reduce quality
      this.reduceQuality();
    } else if (averageFrameTime < targetFrameTime - threshold) {
      // Performance is good, can increase quality
      this.increaseQuality();
    }
  }

  reduceQuality() {
    const qualityLevels = ['ultra', 'high', 'medium', 'low', 'potato'];
    const currentIndex = qualityLevels.indexOf(this.currentQualityLevel);

    if (currentIndex < qualityLevels.length - 1) {
      const newQualityLevel = qualityLevels[currentIndex + 1];
      this.setQualityLevel(newQualityLevel);
      console.log(`Reduced quality to ${newQualityLevel} (FPS: ${this.performanceMetrics.fps})`);
    }
  }

  increaseQuality() {
    const qualityLevels = ['ultra', 'high', 'medium', 'low', 'potato'];
    const currentIndex = qualityLevels.indexOf(this.currentQualityLevel);

    if (currentIndex > 0) {
      const newQualityLevel = qualityLevels[currentIndex - 1];
      this.setQualityLevel(newQualityLevel);
      console.log(`Increased quality to ${newQualityLevel} (FPS: ${this.performanceMetrics.fps})`);
    }
  }

  setQualityLevel(level) {
    if (!this.qualityLevels[level]) {
      console.warn(`Unknown quality level: ${level}`);
      return false;
    }

    this.currentQualityLevel = level;
    this.applyQualitySettings(level);
    this.emit('qualityLevelChanged', { level, metrics: this.performanceMetrics });
    return true;
  }

  applyQualitySettings(level) {
    const settings = this.qualityLevels[level];
    const renderer = this.arvrCore.renderer;

    if (!renderer) return;

    // Pixel ratio
    renderer.setPixelRatio(settings.pixelRatio);

    // Shadow map settings
    if (renderer.shadowMap) {
      renderer.shadowMap.enabled = settings.shadowMapSize > 0;
      if (renderer.shadowMap.enabled) {
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;

        // Update shadow map size for all lights
        this.arvrCore.scene.traverse((object) => {
          if (object.isLight && object.shadow) {
            object.shadow.mapSize.width = settings.shadowMapSize;
            object.shadow.mapSize.height = settings.shadowMapSize;
          }
        });
      }
    }

    // Antialiasing
    // Note: Antialiasing cannot be changed after renderer initialization
    // This would require renderer recreation

    // Texture quality
    this.textureOptimizer.setTextureQuality(settings.textureQuality);

    // LOD bias
    this.lodManager.setLODBias(settings.lodBias);

    // Render scale
    if (renderer.setRenderScale) {
      renderer.setRenderScale(settings.renderScale);
    }

    console.log(`Applied ${level} quality settings`);
  }

  setComfortMode(mode) {
    this.comfortSettings.comfortMode = mode;

    switch (mode) {
      case 'normal':
        this.comfortSettings.snapTurning = false;
        this.comfortSettings.smoothLocomotion = true;
        this.comfortSettings.dynamicFOV = false;
        this.comfortSettings.peripheralVignette = false;
        break;
      case 'comfortable':
        this.comfortSettings.snapTurning = true;
        this.comfortSettings.smoothLocomotion = false;
        this.comfortSettings.dynamicFOV = true;
        this.comfortSettings.peripheralVignette = true;
        this.vignetteStrength = 0.3;
        break;
      case 'maximum':
        this.comfortSettings.snapTurning = true;
        this.comfortSettings.smoothLocomotion = false;
        this.comfortSettings.dynamicFOV = true;
        this.comfortSettings.peripheralVignette = true;
        this.vignetteStrength = 0.6;
        break;
    }

    this.applyComfortSettings();
    this.emit('comfortModeChanged', { mode });
  }

  applyComfortSettings() {
    // Apply vignette
    if (this.motionSicknessSettings.enableVignette && this.vignetteMesh) {
      this.vignetteMaterial.uniforms.strength.value = this.motionSicknessSettings.vignetteStrength;
      this.vignetteMaterial.uniforms.radius.value = this.motionSicknessSettings.vignetteRadius;

      if (this.vignetteMesh.parent !== this.arvrCore.camera) {
        this.arvrCore.camera.add(this.vignetteMesh);
      }
    } else if (this.vignetteMesh && this.vignetteMesh.parent) {
      this.vignetteMesh.parent.remove(this.vignetteMesh);
    }

    // Apply movement speed
    if (this.arvrCore.movementController) {
      this.arvrCore.movementController.setSpeed(this.comfortSettings.movementSpeed);
    }

    // Apply rotation speed
    if (this.arvrCore.rotationController) {
      this.arvrCore.rotationController.setSpeed(this.comfortSettings.rotationSpeed);
    }

    console.log(`Applied ${this.comfortSettings.comfortMode} comfort settings`);
  }

  enableMotionSicknessPrevention(enable) {
    this.motionSicknessSettings.enableVignette = enable;
    this.applyComfortSettings();
  }

  setVignetteStrength(strength) {
    this.motionSicknessSettings.vignetteStrength = Math.max(0, Math.min(1, strength));
    this.applyComfortSettings();
  }

  // Latency optimization
  minimizeLatency() {
    if (!this.options.enableLatencyOptimization) return;

    // Enable motion prediction
    if (this.motionSicknessSettings.enableMotionPrediction) {
      this.enableMotionPrediction();
    }

    // Optimize render pipeline
    this.optimizeRenderPipeline();

    // Reduce input lag
    this.reduceInputLag();

    console.log('Latency optimization enabled');
  }

  enableMotionPrediction() {
    if (this.arvrCore.renderer && this.arvrCore.renderer.xr) {
      // Enable WebXR pose prediction
      this.arvrCore.renderer.xr.setPosePredictionEnabled(true);
    }
  }

  optimizeRenderPipeline() {
    const renderer = this.arvrCore.renderer;

    // Enable instanced rendering where possible
    renderer.capabilities.isWebGL2 = true;

    // Optimize buffer usage
    renderer.info.autoReset = false;

    // Reduce state changes
    renderer.sortObjects = false;

    // Enable frustum culling
    renderer.autoUpdate = false;
  }

  reduceInputLag() {
    // Preload common assets
    this.preloadCriticalAssets();

    // Use event listeners with passive option where possible
    this.setupPassiveEventListeners();

    // Optimize controller input processing
    this.optimizeControllerInput();
  }

  preloadCriticalAssets() {
    // Preload critical models, textures, and sounds
    const criticalAssets = [
      '/assets/models/characters/player.gltf',
      '/assets/models/dice/d20.gltf',
      '/assets/textures/ui/hud.png'
    ];

    criticalAssets.forEach(asset => {
      this.assetStreamingManager?.loadAsset(asset);
    });
  }

  setupPassiveEventListeners() {
    // Use passive event listeners to improve performance
    const passiveOptions = { passive: true };

    window.addEventListener('wheel', () => {}, passiveOptions);
    window.addEventListener('touchstart', () => {}, passiveOptions);
    window.addEventListener('touchmove', () => {}, passiveOptions);
  }

  optimizeControllerInput() {
    // Use requestAnimationFrame for controller input processing
    const processControllerInput = () => {
      // Process controller input here
      requestAnimationFrame(processControllerInput);
    };

    requestAnimationFrame(processControllerInput);
  }

  // Asset streaming
  async streamAsset(url, priority = 'normal') {
    if (!this.assetStreamingManager) {
      console.warn('Asset streaming not initialized');
      return null;
    }

    return this.assetStreamingManager.loadAsset(url, priority);
  }

  preloadAsset(url) {
    return this.streamAsset(url, 'high');
  }

  unloadAsset(url) {
    if (this.assetStreamingManager) {
      this.assetStreamingManager.unloadAsset(url);
    }
  }

  // Memory management
  optimizeMemory() {
    // Force garbage collection if available
    if (window.gc) {
      window.gc();
    }

    // Clear unused assets
    this.clearUnusedAssets();

    // Optimize textures
    this.textureOptimizer.optimizeMemory();

    // Optimize geometries
    this.geometryOptimizer.optimizeMemory();

    console.log('Memory optimization completed');
  }

  clearUnusedAssets() {
    // Remove assets that haven't been used recently
    const now = Date.now();
    const maxAge = 5 * 60 * 1000; // 5 minutes

    for (const [url, asset] of this.assetCache.entries()) {
      if (now - asset.lastUsed > maxAge) {
        this.assetCache.delete(url);
        // Dispose of Three.js resources
        if (asset.texture) asset.texture.dispose();
        if (asset.geometry) asset.geometry.dispose();
      }
    }
  }

  // Frame rate management
  setTargetFPS(fps) {
    this.options.targetFPS = Math.max(30, Math.min(120, fps));

    // Adjust frame timing
    const targetFrameTime = 1000 / this.options.targetFPS;
    this.options.maxRenderTime = targetFrameTime * 0.9; // Use 90% of available time

    console.log(`Target FPS set to ${this.options.targetFPS}`);
  }

  enableFrameRateLimit(enable = true) {
    if (enable) {
      const targetFrameTime = 1000 / this.options.targetFPS;
      let lastFrameTime = performance.now();

      const frameLimiter = () => {
        const currentTime = performance.now();
        const deltaTime = currentTime - lastFrameTime;

        if (deltaTime >= targetFrameTime) {
          lastFrameTime = currentTime - (deltaTime % targetFrameTime);
          this.arvrCore.render();
        }

        requestAnimationFrame(frameLimiter);
      };

      requestAnimationFrame(frameLimiter);
    }
  }

  // Diagnostic tools
  getPerformanceReport() {
    return {
      currentFPS: this.performanceMetrics.fps,
      averageFrameTime: this.performanceMetrics.averageFrameTime,
      worstFrameTime: this.performanceMetrics.worstFrameTime,
      memoryUsage: this.performanceMetrics.memoryUsage,
      drawCalls: this.performanceMetrics.drawCalls,
      triangles: this.performanceMetrics.triangles,
      qualityLevel: this.currentQualityLevel,
      comfortMode: this.comfortSettings.comfortMode,
      adaptiveQualityEnabled: this.adaptiveQualityEnabled
    };
  }

  startPerformanceBenchmark(duration = 10000) {
    const startTime = Date.now();
    const benchmarkData = {
      samples: [],
      minFPS: Infinity,
      maxFPS: 0,
      averageFPS: 0
    };

    const sampleInterval = setInterval(() => {
      const currentTime = Date.now();
      const fps = this.performanceMetrics.fps;

      benchmarkData.samples.push({
        time: currentTime - startTime,
        fps: fps,
        frameTime: this.performanceMetrics.averageFrameTime,
        memory: this.performanceMetrics.memoryUsage
      });

      benchmarkData.minFPS = Math.min(benchmarkData.minFPS, fps);
      benchmarkData.maxFPS = Math.max(benchmarkData.maxFPS, fps);

      if (currentTime - startTime >= duration) {
        clearInterval(sampleInterval);

        // Calculate average FPS
        const totalFPS = benchmarkData.samples.reduce((sum, sample) => sum + sample.fps, 0);
        benchmarkData.averageFPS = totalFPS / benchmarkData.samples.length;

        this.emit('benchmarkCompleted', benchmarkData);
        console.log('Performance benchmark completed:', benchmarkData);
      }
    }, 100);

    return benchmarkData;
  }

  // Update loop
  update(deltaTime) {
    if (!this.isInitialized) return;

    // Update optimization managers
    this.lodManager.update();
    this.cullingManager.update();
    this.assetStreamingManager?.update();

    // Update comfort settings
    if (this.motionSicknessSettings.enableVignette && this.vignetteMesh) {
      // Animate vignette based on movement
      const movementIntensity = this.calculateMovementIntensity();
      const targetStrength = this.motionSicknessSettings.vignetteStrength * movementIntensity;
      this.vignetteMaterial.uniforms.strength.value = THREE.MathUtils.lerp(
        this.vignetteMaterial.uniforms.strength.value,
        targetStrength,
        0.1
      );
    }
  }

  calculateMovementIntensity() {
    // Calculate how fast the user is moving
    let intensity = 0;

    if (this.arvrCore.camera) {
      const velocity = this.arvrCore.camera.userData.velocity || new THREE.Vector3();
      intensity = Math.min(velocity.length() / 5, 1); // Normalize to 0-1
    }

    return intensity;
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
    // Dispose performance observer
    if (this.frameTimeObserver) {
      this.frameTimeObserver.disconnect();
    }

    // Dispose vignette
    if (this.vignetteMesh) {
      this.vignetteMesh.geometry.dispose();
      this.vignetteMaterial.dispose();
    }

    // Dispose optimization managers
    this.lodManager.dispose();
    this.cullingManager.dispose();
    this.textureOptimizer.dispose();
    this.geometryOptimizer.dispose();

    // Dispose asset streaming
    this.assetStreamingManager?.dispose();

    // Clear caches
    this.assetCache.clear();
    this.loadingAssets.clear();

    this.eventListeners.clear();
    this.isInitialized = false;
  }
}

// Supporting optimization classes

class LODManager {
  constructor() {
    this.objects = new Map();
    this.lodBias = 0;
  }

  async initialize(arvrCore) {
    this.arvrCore = arvrCore;
  }

  addLODObject(object, lodLevels) {
    this.objects.set(object.uuid, {
      object: object,
      lodLevels: lodLevels,
      currentLevel: 0
    });
  }

  setLODBias(bias) {
    this.lodBias = bias;
  }

  update() {
    if (!this.arvrCore || !this.arvrCore.camera) return;

    const cameraPosition = this.arvrCore.camera.position;

    for (const lodData of this.objects.values()) {
      const distance = cameraPosition.distanceTo(lodData.object.position);
      const lodLevel = this.calculateLODLevel(distance);

      if (lodLevel !== lodData.currentLevel) {
        this.updateLOD(lodData, lodLevel);
      }
    }
  }

  calculateLODLevel(distance) {
    // Simple LOD calculation based on distance and bias
    const adjustedDistance = distance + this.lodBias * 10;

    if (adjustedDistance < 5) return 0; // Highest detail
    if (adjustedDistance < 15) return 1;
    if (adjustedDistance < 30) return 2;
    return 3; // Lowest detail
  }

  updateLOD(lodData, newLevel) {
    lodData.currentLevel = newLevel;

    // Update object based on LOD level
    if (lodData.object.isLOD) {
      lodData.object.setLevel(newLevel);
    }
  }

  dispose() {
    this.objects.clear();
  }
}

class CullingManager {
  constructor() {
    this.objects = new Set();
    this.frustum = new THREE.Frustum();
    this.cameraMatrix = new THREE.Matrix4();
  }

  async initialize(arvrCore) {
    this.arvrCore = arvrCore;
  }

  addObject(object) {
    this.objects.add(object);
  }

  removeObject(object) {
    this.objects.delete(object);
  }

  update() {
    if (!this.arvrCore || !this.arvrCore.camera) return;

    // Update frustum
    this.cameraMatrix.multiplyMatrices(
      this.arvrCore.camera.projectionMatrix,
      this.arvrCore.camera.matrixWorldInverse
    );
    this.frustum.setFromProjectionMatrix(this.cameraMatrix);

    // Cull objects outside frustum
    for (const object of this.objects) {
      this.cullObject(object);
    }
  }

  cullObject(object) {
    const boundingBox = new THREE.Box3().setFromObject(object);
    const inFrustum = this.frustum.intersectsBox(boundingBox);

    object.visible = inFrustum;
  }

  dispose() {
    this.objects.clear();
  }
}

class TextureOptimizer {
  constructor() {
    this.textures = new Map();
    this.maxTextureSize = 1024;
  }

  async initialize(arvrCore) {
    this.arvrCore = arvrCore;

    // Determine max texture size
    const gl = this.arvrCore.renderer.getContext();
    this.maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
  }

  optimizeTexture(texture) {
    if (texture.image.width > this.maxTextureSize || texture.image.height > this.maxTextureSize) {
      // Resize texture to fit within limits
      this.resizeTexture(texture);
    }

    // Generate mipmaps if needed
    if (!texture.generateMipmaps) {
      texture.generateMipmaps = true;
      texture.needsUpdate = true;
    }
  }

  resizeTexture(texture) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    const maxSize = Math.min(this.maxTextureSize, 1024);
    const scale = Math.min(maxSize / texture.image.width, maxSize / texture.image.height);

    canvas.width = texture.image.width * scale;
    canvas.height = texture.image.height * scale;

    ctx.drawImage(texture.image, 0, 0, canvas.width, canvas.height);

    texture.image = canvas;
    texture.needsUpdate = true;
  }

  setTextureQuality(quality) {
    const scales = {
      'high': 1.0,
      'medium': 0.7,
      'low': 0.5
    };

    const scale = scales[quality] || 0.7;

    for (const texture of this.textures.values()) {
      this.resizeTextureByScale(texture, scale);
    }
  }

  resizeTextureByScale(texture, scale) {
    if (scale >= 1.0) return;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    canvas.width = texture.image.width * scale;
    canvas.height = texture.image.height * scale;

    ctx.drawImage(texture.image, 0, 0, canvas.width, canvas.height);

    texture.image = canvas;
    texture.needsUpdate = true;
  }

  optimizeMemory() {
    // Dispose of unused textures
    for (const [id, texture] of this.textures.entries()) {
      if (texture.userData && texture.userData.lastUsed) {
        const age = Date.now() - texture.userData.lastUsed;
        if (age > 60000) { // 1 minute
          texture.dispose();
          this.textures.delete(id);
        }
      }
    }
  }

  dispose() {
    for (const texture of this.textures.values()) {
      texture.dispose();
    }
    this.textures.clear();
  }
}

class GeometryOptimizer {
  constructor() {
    this.geometries = new Map();
  }

  async initialize(arvrCore) {
    this.arvrCore = arvrCore;
  }

  optimizeGeometry(geometry) {
    // Merge vertices if possible
    if (geometry.attributes.position) {
      geometry = geometry.clone();
      geometry.mergeVertices();
    }

    // Compute normals if missing
    if (!geometry.attributes.normal) {
      geometry.computeVertexNormals();
    }

    // Compute bounding box and sphere
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();
  }

  optimizeMemory() {
    // Dispose of unused geometries
    for (const [id, geometry] of this.geometries.entries()) {
      if (geometry.userData && geometry.userData.lastUsed) {
        const age = Date.now() - geometry.userData.lastUsed;
        if (age > 60000) { // 1 minute
          geometry.dispose();
          this.geometries.delete(id);
        }
      }
    }
  }

  dispose() {
    for (const geometry of this.geometries.values()) {
      geometry.dispose();
    }
    this.geometries.clear();
  }
}

class AssetStreamingManager {
  constructor(options = {}) {
    this.options = options;
    this.loadingQueue = [];
    this.activeLoads = 0;
    this.cache = new Map();
  }

  async initialize() {
    console.log('Asset streaming manager initialized');
  }

  async loadAsset(url, priority = 'normal') {
    // Check cache first
    if (this.cache.has(url)) {
      const asset = this.cache.get(url);
      asset.lastUsed = Date.now();
      return asset;
    }

    // Add to loading queue
    return new Promise((resolve, reject) => {
      this.loadingQueue.push({
        url,
        priority,
        resolve,
        reject
      });

      this.processQueue();
    });
  }

  processQueue() {
    if (this.activeLoads >= this.options.maxConcurrentLoads) return;

    // Sort by priority
    this.loadingQueue.sort((a, b) => {
      const priorities = { 'high': 3, 'normal': 2, 'low': 1 };
      return priorities[b.priority] - priorities[a.priority];
    });

    // Load next asset
    const item = this.loadingQueue.shift();
    if (item) {
      this.activeLoads++;
      this.loadAssetInternal(item);
    }
  }

  async loadAssetInternal(item) {
    try {
      const asset = await this.fetchAsset(item.url);
      this.cache.set(item.url, { ...asset, lastUsed: Date.now() });
      item.resolve(asset);
    } catch (error) {
      item.reject(error);
    } finally {
      this.activeLoads--;
      this.processQueue();
    }
  }

  async fetchAsset(url) {
    // Implementation for fetching assets
    const response = await fetch(url);
    return response;
  }

  unloadAsset(url) {
    if (this.cache.has(url)) {
      const asset = this.cache.get(url);
      if (asset.dispose) {
        asset.dispose();
      }
      this.cache.delete(url);
    }
  }

  update() {
    this.processQueue();
  }

  dispose() {
    this.loadingQueue.length = 0;
    for (const asset of this.cache.values()) {
      if (asset.dispose) {
        asset.dispose();
      }
    }
    this.cache.clear();
  }
}

export default PerformanceOptimization;