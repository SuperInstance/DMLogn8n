/**
 * AR/VR Core System for D&D Mixed Reality Integration
 * Provides foundation classes and utilities for AR/VR experiences
 */

import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { VRButton } from 'three/examples/jsm/webxr/VRButton.js';
import { ARButton } from 'three/examples/jsm/webxr/ARButton.js';
import { XRControllerModelFactory } from 'three/examples/jsm/webxr/XRControllerModelFactory.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader.js';

export class ARVRCore {
  constructor(options = {}) {
    this.options = {
      container: options.container || document.body,
      enableVR: options.enableVR !== false,
      enableAR: options.enableAR !== false,
      enableHandTracking: options.enableHandTracking !== false,
      targetFPS: options.targetFPS || 90,
      antialias: options.antialias !== false,
      alpha: options.alpha !== false,
      ...options
    };

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.clock = new THREE.Clock();
    this.mixers = [];
    this.raycaster = new THREE.Raycaster();
    this.interactiveObjects = [];
    this.controllers = [];
    this.handTracking = null;
    this.spatialAudio = null;
    this.physics = null;

    this.isVR = false;
    this.isAR = false;
    this.isInitialized = false;

    // Performance monitoring
    this.performanceMonitor = {
      frameCount: 0,
      fps: 0,
      lastTime: performance.now(),
      memoryUsage: 0
    };

    // Event system
    this.eventListeners = new Map();

    // Device capabilities
    this.deviceCapabilities = {
      hasVR: false,
      hasAR: false,
      hasHandTracking: false,
      hasSpatialAudio: false,
      deviceType: 'unknown'
    };
  }

  async initialize() {
    try {
      await this.detectDeviceCapabilities();
      await this.setupRenderer();
      await this.setupScene();
      await this.setupLighting();
      await this.setupControls();
      await this.setupInput();
      await this.setupAudio();

      this.isInitialized = true;
      this.emit('initialized', this.deviceCapabilities);

      console.log('AR/VR Core initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize AR/VR Core:', error);
      this.emit('error', error);
      return false;
    }
  }

  async detectDeviceCapabilities() {
    // Check WebXR support
    if ('xr' in navigator) {
      try {
        const isVRSupported = await navigator.xr.isSessionSupported('immersive-vr');
        const isARSupported = await navigator.xr.isSessionSupported('immersive-ar');

        this.deviceCapabilities.hasVR = isVRSupported;
        this.deviceCapabilities.hasAR = isARSupported;
      } catch (error) {
        console.warn('WebXR detection failed:', error);
      }
    }

    // Detect device type
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('oculus') || userAgent.includes('quest')) {
      this.deviceCapabilities.deviceType = 'meta-quest';
    } else if (userAgent.includes('hololens')) {
      this.deviceCapabilities.deviceType = 'hololens';
    } else if (userAgent.includes('iphone') || userAgent.includes('ipad')) {
      this.deviceCapabilities.deviceType = 'ios';
      this.deviceCapabilities.hasAR = true; // ARKit support
    } else if (userAgent.includes('android')) {
      this.deviceCapabilities.deviceType = 'android';
      this.deviceCapabilities.hasAR = true; // ARCore support
    } else {
      this.deviceCapabilities.deviceType = 'desktop';
    }

    // Check hand tracking support
    this.deviceCapabilities.hasHandTracking = 'xr' in navigator &&
      navigator.xr?.requestSession &&
      this.deviceCapabilities.deviceType !== 'desktop';

    // Check spatial audio support
    this.deviceCapabilities.hasSpatialAudio = 'AudioContext' in window &&
      'AudioListener' in window &&
      'PannerNode' in window;
  }

  async setupRenderer() {
    const { width, height } = this.options.container.getBoundingClientRect();

    this.renderer = new THREE.WebGLRenderer({
      antialias: this.options.antialias,
      alpha: this.options.alpha,
      powerPreference: 'high-performance',
      failIfMajorPerformanceCaveat: false
    });

    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1;

    // Enable XR for VR/AR
    this.renderer.xr.enabled = true;

    this.options.container.appendChild(this.renderer.domElement);

    // Add VR button if VR is supported
    if (this.deviceCapabilities.hasVR && this.options.enableVR) {
      const vrButton = VRButton.createButton(this.renderer);
      vrButton.style.position = 'absolute';
      vrButton.style.bottom = '20px';
      vrButton.style.right = '20px';
      this.options.container.appendChild(vrButton);
    }

    // Add AR button if AR is supported
    if (this.deviceCapabilities.hasAR && this.options.enableAR) {
      const arButton = ARButton.createButton(this.renderer);
      arButton.style.position = 'absolute';
      arButton.style.bottom = '20px';
      arButton.style.left = '20px';
      this.options.container.appendChild(arButton);
    }

    // Handle window resize
    window.addEventListener('resize', this.handleResize.bind(this));
  }

  async setupScene() {
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x1a1a2e);

    // Camera setup
    const aspect = window.innerWidth / window.innerHeight;
    this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
    this.camera.position.set(0, 1.6, 3); // Average human eye height

    // Setup XR session management
    this.renderer.xr.addEventListener('sessionstart', () => {
      const session = this.renderer.xr.getSession();
      if (session.environmentBlendMode === 'opaque') {
        this.isVR = true;
        this.isAR = false;
        console.log('VR Session started');
      } else {
        this.isVR = false;
        this.isAR = true;
        console.log('AR Session started');
      }
      this.emit('sessionStart', { isVR: this.isVR, isAR: this.isAR });
    });

    this.renderer.xr.addEventListener('sessionend', () => {
      this.isVR = false;
      this.isAR = false;
      console.log('XR Session ended');
      this.emit('sessionEnd');
    });
  }

  async setupLighting() {
    // Ambient lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    this.scene.add(ambientLight);

    // Main directional light (sun)
    const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
    directionalLight.position.set(5, 10, 7.5);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 50;
    directionalLight.shadow.camera.left = -10;
    directionalLight.shadow.camera.right = 10;
    directionalLight.shadow.camera.top = 10;
    directionalLight.shadow.camera.bottom = -10;
    this.scene.add(directionalLight);

    // Point lights for dungeon atmosphere
    const pointLight1 = new THREE.PointLight(0xff6b6b, 1, 20);
    pointLight1.position.set(-5, 2, 0);
    pointLight1.castShadow = true;
    this.scene.add(pointLight1);

    const pointLight2 = new THREE.PointLight(0x4ecdc4, 1, 20);
    pointLight2.position.set(5, 2, 0);
    pointLight2.castShadow = true;
    this.scene.add(pointLight2);

    // Store lights for dynamic adjustments
    this.lights = {
      ambient: ambientLight,
      directional: directionalLight,
      point: [pointLight1, pointLight2]
    };
  }

  async setupControls() {
    if (!this.isVR && !this.isAR) {
      // Desktop controls
      this.controls = new OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.screenSpacePanning = false;
      this.controls.minDistance = 1;
      this.controls.maxDistance = 50;
      this.controls.maxPolarAngle = Math.PI / 2;
    }
  }

  async setupInput() {
    if (!this.deviceCapabilities.hasVR) return;

    // Setup VR controllers
    const controllerModelFactory = new XRControllerModelFactory();

    for (let i = 0; i < 2; i++) {
      const controller = this.renderer.xr.getController(i);
      controller.addEventListener('select', this.onControllerSelect.bind(this));
      controller.addEventListener('squeeze', this.onControllerSqueeze.bind(this));
      this.scene.add(controller);

      const controllerGrip = this.renderer.xr.getControllerGrip(i);
      const model = controllerModelFactory.createControllerModel(controllerGrip);
      controllerGrip.add(model);
      this.scene.add(controllerGrip);

      this.controllers.push({
        controller,
        grip: controllerGrip,
        model,
        index: i
      });
    }

    // Setup hand tracking if available
    if (this.deviceCapabilities.hasHandTracking && this.options.enableHandTracking) {
      await this.setupHandTracking();
    }
  }

  async setupHandTracking() {
    try {
      // Right hand
      const rightHand = this.renderer.xr.getHand(0);
      rightHand.addEventListener('pinchstart', this.onHandPinchStart.bind(this));
      rightHand.addEventListener('pinchend', this.onHandPinchEnd.bind(this));
      this.scene.add(rightHand);

      // Left hand
      const leftHand = this.renderer.xr.getHand(1);
      leftHand.addEventListener('pinchstart', this.onHandPinchStart.bind(this));
      leftHand.addEventListener('pinchend', this.onHandPinchEnd.bind(this));
      this.scene.add(leftHand);

      this.handTracking = {
        right: rightHand,
        left: leftHand
      };

      console.log('Hand tracking initialized');
    } catch (error) {
      console.warn('Hand tracking setup failed:', error);
    }
  }

  async setupAudio() {
    if (!this.deviceCapabilities.hasSpatialAudio) return;

    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const listener = this.camera.add(new THREE.AudioListener());

      this.spatialAudio = {
        context: audioContext,
        listener: listener
      };

      console.log('Spatial audio initialized');
    } catch (error) {
      console.warn('Spatial audio setup failed:', error);
    }
  }

  onControllerSelect(event) {
    const controller = event.target;
    this.handleSelection(controller);
  }

  onControllerSqueeze(event) {
    const controller = event.target;
    this.handleSqueeze(controller);
  }

  onHandPinchStart(event) {
    const hand = event.target;
    this.handlePinchStart(hand);
  }

  onHandPinchEnd(event) {
    const hand = event.target;
    this.handlePinchEnd(hand);
  }

  handleSelection(controller) {
    // Update raycaster from controller
    this.raycaster.setFromController(controller);
    const intersects = this.raycaster.intersectObjects(this.interactiveObjects);

    if (intersects.length > 0) {
      const object = intersects[0].object;
      this.emit('objectSelected', { object, controller, intersection: intersects[0] });
    }
  }

  handleSqueeze(controller) {
    this.emit('squeeze', { controller });
  }

  handlePinchStart(hand) {
    this.emit('pinchStart', { hand });
  }

  handlePinchEnd(hand) {
    this.emit('pinchEnd', { hand });
  }

  addInteractiveObject(object) {
    this.interactiveObjects.push(object);
    this.scene.add(object);
  }

  removeInteractiveObject(object) {
    const index = this.interactiveObjects.indexOf(object);
    if (index > -1) {
      this.interactiveObjects.splice(index, 1);
      this.scene.remove(object);
    }
  }

  async loadModel(url, options = {}) {
    return new Promise((resolve, reject) => {
      const loader = new GLTFLoader();

      // Optional: Setup Draco loader for compressed models
      if (options.enableDraco) {
        const dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath('/draco/');
        loader.setDRACOLoader(dracoLoader);
      }

      loader.load(
        url,
        (gltf) => {
          // Optimize model
          this.optimizeModel(gltf.scene, options);

          // Setup animations
          if (gltf.animations && gltf.animations.length > 0) {
            const mixer = new THREE.AnimationMixer(gltf.scene);
            gltf.animations.forEach((clip) => {
              mixer.clipAction(clip);
            });
            this.mixers.push(mixer);
          }

          resolve(gltf);
        },
        (progress) => {
          console.log('Loading progress:', (progress.loaded / progress.total * 100) + '%');
        },
        (error) => {
          console.error('Model loading failed:', error);
          reject(error);
        }
      );
    });
  }

  optimizeModel(model, options = {}) {
    model.traverse((child) => {
      if (child.isMesh) {
        // Enable shadows
        child.castShadow = options.castShadow !== false;
        child.receiveShadow = options.receiveShadow !== false;

        // Optimize materials
        if (child.material) {
          child.material.needsUpdate = true;
          if (options.optimizeMaterials) {
            // Material optimization logic here
          }
        }
      }
    });
  }

  handleResize() {
    const { width, height } = this.options.container.getBoundingClientRect();
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  updatePerformance() {
    const now = performance.now();
    const delta = now - this.performanceMonitor.lastTime;

    this.performanceMonitor.frameCount++;

    if (delta >= 1000) {
      this.performanceMonitor.fps = Math.round(
        (this.performanceMonitor.frameCount * 1000) / delta
      );
      this.performanceMonitor.frameCount = 0;
      this.performanceMonitor.lastTime = now;

      // Memory usage if available
      if (performance.memory) {
        this.performanceMonitor.memoryUsage = performance.memory.usedJSHeapSize / 1048576; // MB
      }

      this.emit('performanceUpdate', this.performanceMonitor);
    }
  }

  animate() {
    if (!this.isInitialized) return;

    this.renderer.setAnimationLoop(() => {
      const delta = this.clock.getDelta();

      // Update animations
      this.mixers.forEach(mixer => mixer.update(delta));

      // Update controls
      if (this.controls) {
        this.controls.update();
      }

      // Update performance monitoring
      this.updatePerformance();

      // Render
      this.renderer.render(this.scene, this.camera);
    });
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

  dispose() {
    // Clean up resources
    this.mixers.forEach(mixer => mixer.stopAllAction());
    this.mixers = [];

    if (this.renderer) {
      this.renderer.dispose();
    }

    if (this.spatialAudio?.context) {
      this.spatialAudio.context.close();
    }

    this.eventListeners.clear();
    this.interactiveObjects = [];
    this.controllers = [];
  }
}

export default ARVRCore;