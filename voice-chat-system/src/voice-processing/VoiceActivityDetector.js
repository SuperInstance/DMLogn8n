/**
 * Voice Activity Detector - Detects when someone is speaking
 * Provides reliable voice activity detection with adjustable sensitivity
 */

export class VoiceActivityDetector {
  constructor(audioContext, config = {}) {
    this.audioContext = audioContext;
    this.config = {
      threshold: 0.01,
      attackTime: 0.01,
      releaseTime: 0.1,
      minSpeechDuration: 0.1,
      maxSilenceDuration: 0.5,
      frequencyRange: { min: 80, max: 4000 },
      ...config
    };

    // Detection state
    this.state = {
      isActive: false,
      level: 0,
      frequency: 0,
      startTime: 0,
      lastActiveTime: 0,
      speechDetected: false
    };

    // Audio processing nodes
    this.analyser = null;
    this.scriptProcessor = null;
    this.mediaStream = null;

    // Smoothing and filtering
    this.levelHistory = [];
    this.historySize = 10;
    this.smoothingFactor = 0.8;

    // Frequency analysis
    this.fftSize = 2048;
    this.frequencyBins = null;

    // Event system
    this.eventListeners = new Map();

    // Performance monitoring
    this.metrics = {
      detectionsPerSecond: 0,
      averageLevel: 0,
      averageFrequency: 0
    };
  }

  /**
   * Start voice activity detection on a media stream
   */
  start(mediaStream) {
    try {
      this.mediaStream = mediaStream;

      // Create audio source from stream
      const source = this.audioContext.createMediaStreamSource(mediaStream);

      // Create analyser for frequency analysis
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = this.fftSize;
      this.analyser.smoothingTimeConstant = 0.8;

      // Create script processor for real-time analysis
      this.scriptProcessor = this.audioContext.createScriptProcessor(2048, 1, 1);

      // Set up audio processing chain
      source.connect(this.analyser);
      source.connect(this.scriptProcessor);
      this.scriptProcessor.connect(this.audioContext.destination);

      // Initialize frequency bins
      this.frequencyBins = new Uint8Array(this.analyser.frequencyBinCount);

      // Set up processing callback
      this.scriptProcessor.onaudioprocess = this.processAudio.bind(this);

      // Start performance monitoring
      this.startPerformanceMonitoring();

      this.emit('started');
    } catch (error) {
      console.error('Failed to start voice activity detection:', error);
      throw error;
    }
  }

  /**
   * Stop voice activity detection
   */
  stop() {
    if (this.scriptProcessor) {
      this.scriptProcessor.disconnect();
      this.scriptProcessor = null;
    }

    if (this.analyser) {
      this.analyser.disconnect();
      this.analyser = null;
    }

    this.mediaStream = null;
    this.frequencyBins = null;

    this.stopPerformanceMonitoring();
    this.emit('stopped');
  }

  /**
   * Process audio data for voice activity detection
   */
  processAudio(event) {
    if (!this.analyser || !this.frequencyBins) return;

    // Get frequency data
    this.analyser.getByteFrequencyData(this.frequencyBins);

    // Calculate audio level in voice frequency range
    const level = this.calculateVoiceLevel();
    const frequency = this.calculateDominantFrequency();

    // Update level history for smoothing
    this.updateLevelHistory(level);

    // Smooth the level
    const smoothedLevel = this.getSmoothedLevel();

    // Detect voice activity
    this.detectVoiceActivity(smoothedLevel, frequency);

    // Update metrics
    this.updateMetrics(smoothedLevel, frequency);
  }

  /**
   * Calculate audio level in voice frequency range
   */
  calculateVoiceLevel() {
    const nyquist = this.audioContext.sampleRate / 2;
    const minBin = Math.floor((this.config.frequencyRange.min / nyquist) * this.frequencyBins.length);
    const maxBin = Math.floor((this.config.frequencyRange.max / nyquist) * this.frequencyBins.length);

    let sum = 0;
    let count = 0;

    for (let i = minBin; i < maxBin && i < this.frequencyBins.length; i++) {
      const magnitude = this.frequencyBins[i] / 255; // Normalize to 0-1
      sum += magnitude * magnitude; // Use RMS
      count++;
    }

    return count > 0 ? Math.sqrt(sum / count) : 0;
  }

  /**
   * Calculate dominant frequency in the signal
   */
  calculateDominantFrequency() {
    if (!this.frequencyBins) return 0;

    let maxMagnitude = 0;
    let maxBin = 0;

    for (let i = 0; i < this.frequencyBins.length; i++) {
      if (this.frequencyBins[i] > maxMagnitude) {
        maxMagnitude = this.frequencyBins[i];
        maxBin = i;
      }
    }

    // Convert bin index to frequency
    const nyquist = this.audioContext.sampleRate / 2;
    const binWidth = nyquist / this.frequencyBins.length;
    return maxBin * binWidth;
  }

  /**
   * Update level history for smoothing
   */
  updateLevelHistory(level) {
    this.levelHistory.push(level);

    // Keep history size limited
    if (this.levelHistory.length > this.historySize) {
      this.levelHistory.shift();
    }
  }

  /**
   * Get smoothed level using exponential moving average
   */
  getSmoothedLevel() {
    if (this.levelHistory.length === 0) return 0;

    let smoothedLevel = this.levelHistory[0];

    for (let i = 1; i < this.levelHistory.length; i++) {
      smoothedLevel = (this.smoothingFactor * smoothedLevel) +
                      ((1 - this.smoothingFactor) * this.levelHistory[i]);
    }

    return smoothedLevel;
  }

  /**
   * Detect voice activity based on level and frequency
   */
  detectVoiceActivity(level, frequency) {
    const currentTime = Date.now() / 1000;
    const threshold = this.config.threshold;
    const isAboveThreshold = level > threshold;
    const isVoiceFrequency = frequency >= this.config.frequencyRange.min &&
                            frequency <= this.config.frequencyRange.max;

    const shouldActivate = isAboveThreshold && isVoiceFrequency;

    if (shouldActivate && !this.state.isActive) {
      // Voice activity started
      this.state.isActive = true;
      this.state.startTime = currentTime;

      // Check minimum speech duration
      setTimeout(() => {
        if (this.state.isActive && currentTime - this.state.startTime >= this.config.minSpeechDuration) {
          this.state.speechDetected = true;
          this.emit('speechStarted', {
            time: currentTime,
            level,
            frequency
          });
        }
      }, this.config.minSpeechDuration * 1000);

    } else if (!shouldActivate && this.state.isActive) {
      // Voice activity ended
      this.state.isActive = false;
      this.state.lastActiveTime = currentTime;

      if (this.state.speechDetected) {
        this.state.speechDetected = false;
        this.emit('speechEnded', {
          time: currentTime,
          duration: currentTime - this.state.startTime,
          level,
          frequency
        });
      }
    }

    // Update state
    this.state.level = level;
    this.state.frequency = frequency;

    // Emit continuous voice activity events
    this.emit('voiceActivity', {
      isActive: this.state.isActive,
      level,
      frequency,
      time: currentTime
    });
  }

  /**
   * Start performance monitoring
   */
  startPerformanceMonitoring() {
    this.performanceInterval = setInterval(() => {
      this.calculatePerformanceMetrics();
    }, 1000);
  }

  /**
   * Stop performance monitoring
   */
  stopPerformanceMonitoring() {
    if (this.performanceInterval) {
      clearInterval(this.performanceInterval);
      this.performanceInterval = null;
    }
  }

  /**
   * Calculate performance metrics
   */
  calculatePerformanceMetrics() {
    // Calculate average level over the last second
    if (this.levelHistory.length > 0) {
      const avgLevel = this.levelHistory.reduce((sum, level) => sum + level, 0) / this.levelHistory.length;
      this.metrics.averageLevel = avgLevel;
    }

    // Calculate average frequency
    this.metrics.averageFrequency = this.state.frequency;

    // Calculate detections per second (simplified)
    this.metrics.detectionsPerSecond = this.state.isActive ? 1 : 0;
  }

  /**
   * Update metrics
   */
  updateMetrics(level, frequency) {
    this.metrics.currentLevel = level;
    this.metrics.currentFrequency = frequency;
  }

  /**
   * Adjust detection threshold
   */
  setThreshold(threshold) {
    this.config.threshold = Math.max(0, Math.min(1, threshold));
    this.emit('thresholdChanged', { threshold: this.config.threshold });
  }

  /**
   * Adjust frequency range
   */
  setFrequencyRange(min, max) {
    this.config.frequencyRange = { min, max };
    this.emit('frequencyRangeChanged', { min, max });
  }

  /**
   * Adjust timing parameters
   */
  setTimingParameters(attackTime, releaseTime, minSpeechDuration, maxSilenceDuration) {
    this.config.attackTime = attackTime;
    this.config.releaseTime = releaseTime;
    this.config.minSpeechDuration = minSpeechDuration;
    this.config.maxSilenceDuration = maxSilenceDuration;

    this.emit('timingParametersChanged', {
      attackTime,
      releaseTime,
      minSpeechDuration,
      maxSilenceDuration
    });
  }

  /**
   * Get current detection state
   */
  getState() {
    return {
      ...this.state,
      config: { ...this.config },
      metrics: { ...this.metrics }
    };
  }

  /**
   * Get performance metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      state: {
        isActive: this.state.isActive,
        speechDetected: this.state.speechDetected,
        uptime: Date.now() / 1000 - (this.state.startTime || 0)
      }
    };
  }

  /**
   * Calibrate threshold based on ambient noise
   */
  async calibrateThreshold(duration = 3000) {
    if (!this.analyser) {
      throw new Error('Voice activity detector not started');
    }

    this.emit('calibrationStarted');

    const levels = [];
    const startTime = Date.now();

    return new Promise((resolve) => {
      const collectSample = () => {
        if (this.analyser && this.frequencyBins) {
          const level = this.calculateVoiceLevel();
          levels.push(level);
        }

        if (Date.now() - startTime < duration) {
          setTimeout(collectSample, 100);
        } else {
          // Calculate noise floor
          const avgLevel = levels.reduce((sum, level) => sum + level, 0) / levels.length;
          const maxLevel = Math.max(...levels);
          const suggestedThreshold = avgLevel + (maxLevel - avgLevel) * 0.5;

          this.setThreshold(suggestedThreshold);

          this.emit('calibrationComplete', {
            averageLevel: avgLevel,
            maxLevel,
            suggestedThreshold
          });

          resolve({
            averageLevel: avgLevel,
            maxLevel,
            suggestedThreshold
          });
        }
      };

      collectSample();
    });
  }

  /**
   * Export detection data for analysis
   */
  exportDetectionData(duration = 10000) {
    return new Promise((resolve) => {
      const data = {
        timestamp: Date.now(),
        duration,
        samples: [],
        config: { ...this.config }
      };

      const startTime = Date.now();
      const sampleInterval = 100; // 10 samples per second

      const collectSample = () => {
        if (Date.now() - startTime < duration) {
          data.samples.push({
            time: Date.now() - startTime,
            level: this.state.level,
            frequency: this.state.frequency,
            isActive: this.state.isActive,
            speechDetected: this.state.speechDetected
          });

          setTimeout(collectSample, sampleInterval);
        } else {
          resolve(data);
        }
      };

      collectSample();
    });
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
          console.error(`Error in voice activity detector event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Destroy the voice activity detector
   */
  destroy() {
    this.stop();
    this.levelHistory = [];
    this.eventListeners.clear();
  }
}