/**
 * Mobile Voice Adapter - Adapts voice chat system for mobile devices
 * Provides mobile-specific optimizations, battery management, and native integration
 */

export class MobileVoiceAdapter {
  constructor(config = {}) {
    this.config = {
      // Mobile-specific settings
      batteryOptimization: true,
      adaptiveBitrate: true,
      optimizedCodecs: true,
      backgroundMode: false,
      hapticFeedback: true,
      touchOptimized: true,

      // Performance settings
      lowLatencyMode: true,
      reducedQualityMode: false,
      adaptiveQuality: true,
      memoryOptimization: true,

      // Audio settings for mobile
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      bluetoothSupport: true,
      speakerphoneSupport: true,

      // Network optimization
      networkAware: true,
      bandwidthAdaptation: true,
      offlineSupport: false,

      // Native integration
      cordovaEnabled: false,
      nativeAudioProcessing: false,
      deviceSpecificOptimizations: true,

      ...config
    };

    // Mobile device detection and capabilities
    this.deviceInfo = this.detectDevice();
    this.capabilities = this.assessCapabilities();

    // Audio context optimization
    this.audioContext = null;
    this.optimizedAudioSettings = null;

    // Battery and performance monitoring
    this.batteryMonitor = null;
    this.performanceMonitor = null;

    // Network monitoring
    this.networkMonitor = null;
    this.connectionQuality = 'good';

    // Native integration
    this.nativeAudio = null;
    this.hapticEngine = null;

    // Mobile UI components
    this.touchControls = null;
    this.voiceUI = null;

    // State management
    this.state = {
      isBackgrounded: false,
      isLowPowerMode: false,
      isBluetoothConnected: false,
      isSpeakerphoneActive: false,
      currentCodec: 'opus',
      audioRoute: 'earpiece'
    };

    // Event system
    this.eventListeners = new Map();

    // Performance metrics
    this.metrics = {
      batteryLevel: 1.0,
      cpuUsage: 0,
      memoryUsage: 0,
      networkLatency: 0,
      audioQuality: 1.0,
      adaptationEvents: 0
    };
  }

  /**
   * Initialize mobile voice adapter
   */
  async initialize() {
    try {
      // Initialize device-specific optimizations
      await this.initializeDeviceOptimizations();

      // Initialize battery monitoring
      if (this.config.batteryOptimization) {
        await this.initializeBatteryMonitoring();
      }

      // Initialize network monitoring
      if (this.config.networkAware) {
        await this.initializeNetworkMonitoring();
      }

      // Initialize native audio processing
      if (this.config.nativeAudioProcessing) {
        await this.initializeNativeAudio();
      }

      // Initialize haptic feedback
      if (this.config.hapticFeedback) {
        await this.initializeHapticFeedback();
      }

      // Initialize touch controls
      if (this.config.touchOptimized) {
        await this.initializeTouchControls();
      }

      // Set up event listeners for mobile-specific events
      this.setupMobileEventListeners();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize mobile voice adapter:', error);
      throw error;
    }
  }

  /**
   * Detect mobile device and capabilities
   */
  detectDevice() {
    const userAgent = navigator.userAgent;
    const platform = navigator.platform;

    const deviceInfo = {
      isMobile: /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent),
      isAndroid: /Android/i.test(userAgent),
      isIOS: /iPhone|iPad|iPod/i.test(userAgent),
      isTablet: /iPad|Android/i.test(userAgent) && window.innerWidth > 768,
      userAgent,
      platform,
      screenWidth: window.screen.width,
      screenHeight: window.screen.height,
      pixelRatio: window.devicePixelRatio || 1,
      memory: navigator.deviceMemory || 4,
      cores: navigator.hardwareConcurrency || 4
    };

    // Device-specific optimizations
    if (deviceInfo.isAndroid) {
      deviceInfo.os = 'android';
      deviceInfo.version = this.getAndroidVersion(userAgent);
    } else if (deviceInfo.isIOS) {
      deviceInfo.os = 'ios';
      deviceInfo.version = this.getIOSVersion(userAgent);
    }

    return deviceInfo;
  }

  /**
   * Get Android version from user agent
   */
  getAndroidVersion(userAgent) {
    const match = userAgent.match(/Android (\d+(?:\.\d+)?)/);
    return match ? parseFloat(match[1]) : null;
  }

  /**
   * Get iOS version from user agent
   */
  getIOSVersion(userAgent) {
    const match = userAgent.match(/OS (\d+(?:_\d+)?)/);
    return match ? parseFloat(match[1].replace(/_/g, '.')) : null;
  }

  /**
   * Assess device capabilities
   */
  assessCapabilities() {
    const capabilities = {
      webAudio: !!(window.AudioContext || window.webkitAudioContext),
      webRTC: !!(window.RTCPeerConnection || window.webkitRTCPeerConnection),
      mediaDevices: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
      audioWorklet: !!(window.AudioContext && window.AudioContext.prototype.audioWorklet),
      hapticFeedback: 'vibrate' in navigator,
      battery: 'getBattery' in navigator,
      network: 'connection' in navigator,
      fullscreen: 'fullscreenEnabled' in document,
      touch: 'ontouchstart' in window,
      deviceOrientation: 'DeviceOrientationEvent' in window,
      geolocation: 'geolocation' in navigator,
      bluetooth: 'bluetooth' in navigator
    };

    // Performance capabilities
    capabilities.performance = {
      lowLatency: capabilities.webAudio,
      highQuality: this.deviceInfo.memory > 2 && this.deviceInfo.cores > 2,
      optimizedCodecs: capabilities.webRTC
    };

    return capabilities;
  }

  /**
   * Initialize device-specific optimizations
   */
  async initializeDeviceOptimizations() {
    // Android-specific optimizations
    if (this.deviceInfo.isAndroid) {
      await this.initializeAndroidOptimizations();
    }

    // iOS-specific optimizations
    if (this.deviceInfo.isIOS) {
      await this.initializeIOSOptimizations();
    }

    // Generic mobile optimizations
    await this.initializeGenericMobileOptimizations();
  }

  /**
   * Initialize Android-specific optimizations
   */
  async initializeAndroidOptimizations() {
    // Optimize for Android audio subsystem
    this.optimizedAudioSettings = {
      sampleRate: this.deviceInfo.version >= 10 ? 48000 : 16000,
      bufferSize: 2048,
      channelCount: 1, // Mono to save bandwidth
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true
    };

    // Configure for Android-specific codecs
    if (this.config.optimizedCodecs) {
      this.state.currentCodec = this.deviceInfo.version >= 12 ? 'opus' : 'pcmu';
    }

    // Android battery optimization
    if (this.config.batteryOptimization) {
      this.enableAndroidBatteryOptimization();
    }
  }

  /**
   * Initialize iOS-specific optimizations
   */
  async initializeIOSOptimizations() {
    // Optimize for iOS audio subsystem
    this.optimizedAudioSettings = {
      sampleRate: this.deviceInfo.version >= 14 ? 48000 : 16000,
      bufferSize: 4096, // iOS prefers larger buffers
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: false // iOS handles gain differently
    };

    // iOS-specific codec optimization
    if (this.config.optimizedCodecs) {
      this.state.currentCodec = 'opus'; // iOS has good Opus support
    }

    // iOS background processing
    if (this.config.backgroundMode) {
      this.enableIOSBackgroundMode();
    }
  }

  /**
   * Initialize generic mobile optimizations
   */
  async initializeGenericMobileOptimizations() {
    // Memory optimization
    if (this.config.memoryOptimization) {
      this.enableMemoryOptimization();
    }

    // Network adaptation
    if (this.config.bandwidthAdaptation) {
      this.enableBandwidthAdaptation();
    }

    // Adaptive quality
    if (this.config.adaptiveQuality) {
      this.enableAdaptiveQuality();
    }
  }

  /**
   * Initialize battery monitoring
   */
  async initializeBatteryMonitoring() {
    if (!this.capabilities.battery) {
      console.warn('Battery API not available');
      return;
    }

    try {
      this.batteryMonitor = await navigator.getBattery();

      // Set up battery event listeners
      this.batteryMonitor.addEventListener('levelchange', this.handleBatteryLevelChange.bind(this));
      this.batteryMonitor.addEventListener('chargingchange', this.handleChargingChange.bind(this));

      this.metrics.batteryLevel = this.batteryMonitor.level;
      this.state.isLowPowerMode = this.batteryMonitor.level < 0.2 && !this.batteryMonitor.charging;

      this.emit('batteryMonitoringInitialized');
    } catch (error) {
      console.warn('Failed to initialize battery monitoring:', error);
    }
  }

  /**
   * Initialize network monitoring
   */
  async initializeNetworkMonitoring() {
    if (!this.capabilities.network) {
      console.warn('Network Information API not available');
      return;
    }

    try {
      this.networkMonitor = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

      if (this.networkMonitor) {
        this.networkMonitor.addEventListener('change', this.handleNetworkChange.bind(this));

        this.updateConnectionQuality();
        this.emit('networkMonitoringInitialized');
      }
    } catch (error) {
      console.warn('Failed to initialize network monitoring:', error);
    }
  }

  /**
   * Initialize native audio processing
   */
  async initializeNativeAudio() {
    // Check for Cordova/Capacitor
    if (window.cordova || window.Capacitor) {
      this.config.cordovaEnabled = true;
      await this.initializeCordovaAudio();
    }

    // Initialize Web Audio API with mobile optimizations
    if (this.capabilities.webAudio) {
      await this.initializeWebAudioMobile();
    }
  }

  /**
   * Initialize Cordova audio plugins
   */
  async initializeCordovaAudio() {
    try {
      // Initialize native audio processing if available
      if (window.plugins && window.plugins.NativeAudio) {
        this.nativeAudio = window.plugins.NativeAudio;
        this.emit('nativeAudioInitialized');
      }

      // Initialize haptic feedback
      if (window.plugins && window.plugins.notification && window.plugins.notification.vibrate) {
        this.hapticEngine = window.plugins.notification.vibrate;
        this.emit('hapticEngineInitialized');
      }
    } catch (error) {
      console.warn('Failed to initialize Cordova audio:', error);
    }
  }

  /**
   * Initialize Web Audio API with mobile optimizations
   */
  async initializeWebAudioMobile() {
    // Create audio context with mobile-specific settings
    const AudioContext = window.AudioContext || window.webkitAudioContext;

    try {
      this.audioContext = new AudioContext({
        latencyHint: this.config.lowLatencyMode ? 'interactive' : 'balanced',
        sampleRate: this.optimizedAudioSettings?.sampleRate || 16000
      });

      // Handle iOS audio context suspension
      if (this.deviceInfo.isIOS) {
        this.setupIOSAudioContext();
      }

      this.emit('webAudioInitialized');
    } catch (error) {
      console.error('Failed to initialize Web Audio API:', error);
    }
  }

  /**
   * Setup iOS audio context handling
   */
  setupIOSAudioContext() {
    // iOS requires user interaction to start audio context
    const resumeAudioContext = () => {
      if (this.audioContext && this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }
    };

    // Add event listeners for user interaction
    document.addEventListener('touchstart', resumeAudioContext, { once: true });
    document.addEventListener('touchend', resumeAudioContext, { once: true });
  }

  /**
   * Initialize haptic feedback
   */
  async initializeHapticFeedback() {
    if (!this.capabilities.hapticFeedback) {
      console.warn('Haptic feedback not available');
      return;
    }

    this.hapticEngine = {
      vibrate: (pattern) => {
        if (navigator.vibrate) {
          navigator.vibrate(pattern);
        }
      }
    };

    this.emit('hapticFeedbackInitialized');
  }

  /**
   * Initialize touch controls
   */
  async initializeTouchControls() {
    // Create touch-optimized voice controls
    this.touchControls = {
      pushToTalkButton: null,
      muteButton: null,
      speakerButton: null,
      settingsButton: null
    };

    // Set up touch event handlers
    this.setupTouchControls();

    this.emit('touchControlsInitialized');
  }

  /**
   * Setup touch controls for mobile interface
   */
  setupTouchControls() {
    // Push-to-talk button
    const pushToTalkButton = document.getElementById('push-to-talk');
    if (pushToTalkButton) {
      pushToTalkButton.addEventListener('touchstart', this.handlePushToTalkStart.bind(this));
      pushToTalkButton.addEventListener('touchend', this.handlePushToTalkEnd.bind(this));
      pushToTalkButton.addEventListener('touchcancel', this.handlePushToTalkEnd.bind(this));
    }

    // Mute button
    const muteButton = document.getElementById('mute-button');
    if (muteButton) {
      muteButton.addEventListener('click', this.handleMuteToggle.bind(this));
    }

    // Speakerphone button
    const speakerButton = document.getElementById('speaker-button');
    if (speakerButton) {
      speakerButton.addEventListener('click', this.handleSpeakerToggle.bind(this));
    }
  }

  /**
   * Setup mobile event listeners
   */
  setupMobileEventListeners() {
    // Handle visibility change (app backgrounding)
    document.addEventListener('visibilitychange', this.handleVisibilityChange.bind(this));

    // Handle page visibility
    document.addEventListener('pagehide', this.handlePageHide.bind(this));
    document.addEventListener('pageshow', this.handlePageShow.bind(this));

    // Handle orientation change
    window.addEventListener('orientationchange', this.handleOrientationChange.bind(this));

    // Handle touch events for voice activation
    document.addEventListener('touchstart', this.handleTouchStart.bind(this));

    // Handle device motion for activity detection
    if (this.capabilities.deviceOrientation) {
      window.addEventListener('devicemotion', this.handleDeviceMotion.bind(this));
    }
  }

  /**
   * Get optimized audio constraints for mobile
   */
  getAudioConstraints() {
    const constraints = {
      audio: {
        sampleRate: this.optimizedAudioSettings?.sampleRate || 16000,
        channelCount: this.optimizedAudioSettings?.channelCount || 1,
        echoCancellation: this.optimizedAudioSettings?.echoCancellation,
        noiseSuppression: this.optimizedAudioSettings?.noiseSuppression,
        autoGainControl: this.optimizedAudioSettings?.autoGainControl
      },
      video: false
    };

    // Apply device-specific optimizations
    if (this.deviceInfo.isAndroid) {
      constraints.audio.echoCancellation = true;
      constraints.audio.noiseSuppression = true;
    }

    if (this.deviceInfo.isIOS) {
      constraints.audio.autoGainControl = false;
    }

    // Apply adaptive quality based on conditions
    if (this.state.isLowPowerMode || this.connectionQuality === 'poor') {
      constraints.audio.sampleRate = 8000;
      constraints.audio.channelCount = 1;
    }

    return constraints;
  }

  /**
   * Handle battery level change
   */
  handleBatteryLevelChange(event) {
    const level = event.target.level;
    this.metrics.batteryLevel = level;

    // Update low power mode
    const wasLowPowerMode = this.state.isLowPowerMode;
    this.state.isLowPowerMode = level < 0.2 && !event.target.charging;

    if (!wasLowPowerMode && this.state.isLowPowerMode) {
      this.enableLowPowerMode();
    } else if (wasLowPowerMode && !this.state.isLowPowerMode) {
      this.disableLowPowerMode();
    }

    this.emit('batteryLevelChanged', { level, isLowPowerMode: this.state.isLowPowerMode });
  }

  /**
   * Handle charging state change
   */
  handleChargingChange(event) {
    const isCharging = event.target.charging;

    // Update low power mode based on charging state
    const wasLowPowerMode = this.state.isLowPowerMode;
    this.state.isLowPowerMode = !isCharging && event.target.level < 0.2;

    if (!wasLowPowerMode && this.state.isLowPowerMode) {
      this.enableLowPowerMode();
    } else if (wasLowPowerMode && !this.state.isLowPowerMode) {
      this.disableLowPowerMode();
    }

    this.emit('chargingStateChanged', { isCharging, isLowPowerMode: this.state.isLowPowerMode });
  }

  /**
   * Handle network connection change
   */
  handleNetworkChange() {
    this.updateConnectionQuality();
    this.adaptToNetworkConditions();
    this.emit('networkChanged', { quality: this.connectionQuality });
  }

  /**
   * Update connection quality assessment
   */
  updateConnectionQuality() {
    if (!this.networkMonitor) return;

    const connection = this.networkMonitor;
    let quality = 'unknown';

    if (connection.effectiveType) {
      switch (connection.effectiveType) {
        case '4g':
          quality = 'excellent';
          break;
        case '3g':
          quality = 'good';
          break;
        case '2g':
          quality = 'poor';
          break;
        case 'slow-2g':
          quality = 'very-poor';
          break;
      }
    }

    // Consider downlink and RTT if available
    if (connection.downlink && connection.rtt) {
      if (connection.downlink > 2 && connection.rtt < 150) {
        quality = 'excellent';
      } else if (connection.downlink > 1 && connection.rtt < 300) {
        quality = 'good';
      } else if (connection.downlink > 0.5 && connection.rtt < 600) {
        quality = 'fair';
      } else {
        quality = 'poor';
      }
    }

    this.connectionQuality = quality;
  }

  /**
   * Adapt to network conditions
   */
  adaptToNetworkConditions() {
    if (!this.config.bandwidthAdaptation) return;

    const adaptations = [];

    switch (this.connectionQuality) {
      case 'excellent':
        // High quality settings
        if (this.optimizedAudioSettings) {
          this.optimizedAudioSettings.sampleRate = 48000;
          this.optimizedAudioSettings.channelCount = 2;
        }
        this.state.currentCodec = 'opus';
        break;

      case 'good':
        // Balanced settings
        if (this.optimizedAudioSettings) {
          this.optimizedAudioSettings.sampleRate = 24000;
          this.optimizedAudioSettings.channelCount = 1;
        }
        this.state.currentCodec = 'opus';
        break;

      case 'fair':
        // Reduced quality
        if (this.optimizedAudioSettings) {
          this.optimizedAudioSettings.sampleRate = 16000;
          this.optimizedAudioSettings.channelCount = 1;
        }
        this.state.currentCodec = 'opus';
        break;

      case 'poor':
      case 'very-poor':
        // Low quality settings
        if (this.optimizedAudioSettings) {
          this.optimizedAudioSettings.sampleRate = 8000;
          this.optimizedAudioSettings.channelCount = 1;
        }
        this.state.currentCodec = 'pcmu'; // Fallback to more compatible codec
        break;
    }

    this.metrics.adaptationEvents++;
    this.emit('networkAdaptation', { quality: this.connectionQuality, adaptations });
  }

  /**
   * Handle visibility change (app backgrounding)
   */
  handleVisibilityChange() {
    if (document.hidden) {
      this.state.isBackgrounded = true;
      this.handleAppBackgrounded();
    } else {
      this.state.isBackgrounded = false;
      this.handleAppForegrounded();
    }
  }

  /**
   * Handle app backgrounded
   */
  handleAppBackgrounded() {
    // Reduce audio quality to save battery
    if (this.config.batteryOptimization) {
      this.enableBackgroundOptimizations();
    }

    // Pause non-essential audio processing
    if (this.audioContext && this.audioContext.state === 'running') {
      this.audioContext.suspend();
    }

    this.emit('appBackgrounded');
  }

  /**
   * Handle app foregrounded
   */
  handleAppForegrounded() {
    // Restore normal audio quality
    if (this.config.batteryOptimization) {
      this.disableBackgroundOptimizations();
    }

    // Resume audio processing
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }

    this.emit('appForegrounded');
  }

  /**
   * Handle page hide
   */
  handlePageHide() {
    // Cleanup resources when page is hidden
    this.cleanup();
  }

  /**
   * Handle page show
   */
  handlePageShow() {
    // Reinitialize when page is shown
    this.initialize();
  }

  /**
   * Handle orientation change
   */
  handleOrientationChange() {
    // Update UI for new orientation
    this.emit('orientationChanged', {
      orientation: window.orientation || (window.innerWidth > window.innerHeight ? 90 : 0)
    });
  }

  /**
   * Handle push-to-talk start
   */
  handlePushToTalkStart(event) {
    event.preventDefault();
    this.emit('pushToTalkStart');

    // Haptic feedback
    if (this.config.hapticFeedback && this.hapticEngine) {
      this.hapticEngine.vibrate(10);
    }
  }

  /**
   * Handle push-to-talk end
   */
  handlePushToTalkEnd(event) {
    event.preventDefault();
    this.emit('pushToTalkEnd');
  }

  /**
   * Handle mute toggle
   */
  handleMuteToggle(event) {
    event.preventDefault();
    this.emit('muteToggle');

    // Haptic feedback
    if (this.config.hapticFeedback && this.hapticEngine) {
      this.hapticEngine.vibrate(20);
    }
  }

  /**
   * Handle speaker toggle
   */
  handleSpeakerToggle(event) {
    event.preventDefault();
    this.state.isSpeakerphoneActive = !this.state.isSpeakerphoneActive;
    this.emit('speakerToggle', { isActive: this.state.isSpeakerphoneActive });

    // Haptic feedback
    if (this.config.hapticFeedback && this.hapticEngine) {
      this.hapticEngine.vibrate(15);
    }
  }

  /**
   * Handle touch start
   */
  handleTouchStart(event) {
    // Could be used for voice activation or UI feedback
    this.emit('touchStart', event);
  }

  /**
   * Handle device motion
   */
  handleDeviceMotion(event) {
    // Could be used for activity detection or UI responsiveness
    this.emit('deviceMotion', {
      acceleration: event.acceleration,
      rotationRate: event.rotationRate,
      interval: event.interval
    });
  }

  /**
   * Enable low power mode
   */
  enableLowPowerMode() {
    // Reduce audio quality
    if (this.optimizedAudioSettings) {
      this.optimizedAudioSettings.sampleRate = 8000;
      this.optimizedAudioSettings.channelCount = 1;
    }

    // Disable non-essential features
    this.config.adaptiveQuality = true;
    this.config.bandwidthAdaptation = true;

    this.emit('lowPowerModeEnabled');
  }

  /**
   * Disable low power mode
   */
  disableLowPowerMode() {
    // Restore normal quality
    this.updateConnectionQuality();

    // Re-enable features
    this.config.adaptiveQuality = true; // Keep adaptive quality
    this.config.bandwidthAdaptation = true;

    this.emit('lowPowerModeDisabled');
  }

  /**
   * Enable background optimizations
   */
  enableBackgroundOptimizations() {
    // Suspend audio processing
    if (this.audioContext && this.audioContext.state === 'running') {
      this.audioContext.suspend();
    }

    // Reduce network activity
    this.state.currentCodec = 'pcmu';

    this.emit('backgroundOptimizationsEnabled');
  }

  /**
   * Disable background optimizations
   */
  disableBackgroundOptimizations() {
    // Resume audio processing
    if (this.audioContext && this.audioContext.state === 'suspended') {
      this.audioContext.resume();
    }

    // Restore normal network settings
    this.updateConnectionQuality();

    this.emit('backgroundOptimizationsDisabled');
  }

  /**
   * Enable memory optimization
   */
  enableMemoryOptimization() {
    // Reduce buffer sizes
    if (this.optimizedAudioSettings) {
      this.optimizedAudioSettings.bufferSize = 1024;
    }

    // Implement garbage collection hints
    if (window.gc) {
      window.gc();
    }

    this.emit('memoryOptimizationEnabled');
  }

  /**
   * Enable bandwidth adaptation
   */
  enableBandwidthAdaptation() {
    // Monitor network and adapt accordingly
    setInterval(() => {
      this.adaptToNetworkConditions();
    }, 5000); // Check every 5 seconds

    this.emit('bandwidthAdaptationEnabled');
  }

  /**
   * Enable adaptive quality
   */
  enableAdaptiveQuality() {
    // Monitor performance and adapt quality
    setInterval(() => {
      this.adaptToPerformanceConditions();
    }, 2000); // Check every 2 seconds

    this.emit('adaptiveQualityEnabled');
  }

  /**
   * Adapt to performance conditions
   */
  adaptToPerformanceConditions() {
    if (!this.config.adaptiveQuality) return;

    // Monitor memory usage and adapt
    if (performance && performance.memory) {
      const memoryUsage = performance.memory.usedJSHeapSize / performance.memory.jsHeapSizeLimit;
      this.metrics.memoryUsage = memoryUsage;

      if (memoryUsage > 0.8) {
        // High memory usage - reduce quality
        this.enableLowPowerMode();
      }
    }

    // Monitor CPU usage and adapt
    // (This would require performance monitoring API)
  }

  /**
   * Enable Android battery optimization
   */
  enableAndroidBatteryOptimization() {
    // Android-specific battery optimizations
    if (window.android && window.android.enableBatteryOptimization) {
      window.android.enableBatteryOptimization();
    }
  }

  /**
   * Enable iOS background mode
   */
  enableIOSBackgroundMode() {
    // iOS-specific background processing
    if (window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.enableBackgroundMode) {
      window.webkit.messageHandlers.enableBackgroundMode.postMessage({});
    }
  }

  /**
   * Trigger haptic feedback
   */
  triggerHapticFeedback(pattern) {
    if (this.config.hapticFeedback && this.hapticEngine) {
      this.hapticEngine.vibrate(pattern);
    }
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      deviceInfo: { ...this.deviceInfo },
      capabilities: { ...this.capabilities },
      state: { ...this.state },
      connectionQuality: this.connectionQuality,
      audioSettings: this.optimizedAudioSettings
    };
  }

  /**
   * Event emitter methods
   */
  on(event, callback) {
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in mobile adapter event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup mobile adapter
   */
  cleanup() {
    // Stop monitoring
    if (this.batteryMonitor) {
      // Remove battery event listeners
    }

    if (this.networkMonitor) {
      // Remove network event listeners
    }

    // Cleanup audio context
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
    }

    // Clear event listeners
    this.eventListeners.clear();
  }
}