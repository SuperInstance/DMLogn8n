/**
 * Spatial Audio Engine - Creates immersive 3D audio experiences
 * Handles position-based audio panning, distance attenuation, and environmental effects
 */

import { AudioPositionTracker } from './AudioPositionTracker.js';
import { RoomAcousticsSimulator } from './RoomAcousticsSimulator.js';
import { EnvironmentalAudioEffects } from './EnvironmentalAudioEffects.js';

export class SpatialAudioEngine {
  constructor(audioContext, config = {}) {
    this.audioContext = audioContext;
    this.config = {
      maxDistance: 100,
      rolloffFactor: 1.0,
      distanceModel: 'inverse', // linear, inverse, exponential
      coneInnerAngle: 360,
      coneOuterAngle: 360,
      coneOuterGain: 0,
      dopplerFactor: 1.0,
      speedOfSound: 343.0, // m/s
      ...config
    };

    // Audio nodes
    this.masterGain = audioContext.createGain();
    this.listener = audioContext.listener;

    // Spatial audio sources
    this.spatialSources = new Map();

    // Room acoustics
    this.roomAcoustics = new RoomAcousticsSimulator(audioContext, config.roomSize || 'medium');
    this.environmentalEffects = new EnvironmentalAudioEffects(audioContext);

    // Position tracking
    this.positionTracker = new AudioPositionTracker();

    // Performance optimization
    this.workletProcessors = new Map();
    this.analyser = audioContext.createAnalyser();
    this.analyser.fftSize = 256;
    this.analyser.connect(this.masterGain);

    // Connect to destination
    this.masterGain.connect(audioContext.destination);

    // Event system
    this.eventListeners = new Map();

    // Initialize listener position
    this.setListenerPosition({ x: 0, y: 0, z: 0 });
    this.setListenerOrientation({ x: 0, y: 0, z: -1 }, { x: 0, y: 1, z: 0 });

    // Performance metrics
    this.metrics = {
      activeSources: 0,
      cpuUsage: 0,
      memoryUsage: 0
    };
  }

  /**
   * Initialize the spatial audio engine
   */
  async initialize() {
    try {
      // Load audio worklets
      await this.loadSpatialAudioWorklets();

      // Initialize room acoustics
      await this.roomAcoustics.initialize();

      // Initialize environmental effects
      await this.environmentalEffects.initialize();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize spatial audio engine:', error);
      throw error;
    }
  }

  /**
   * Load spatial audio worklets
   */
  async loadSpatialAudioWorklets() {
    const worklets = [
      'spatial-audio-processor.js',
      'distance-attenuator.js',
      'doppler-processor.js'
    ];

    for (const worklet of worklets) {
      try {
        await this.audioContext.audioWorklet.addModule(`/worklets/${worklets}`);
        this.workletProcessors.set(worklet, true);
      } catch (error) {
        console.warn(`Failed to load worklet ${worklet}:`, error);
      }
    }
  }

  /**
   * Create a spatial audio source
   */
  async createSpatialSource(sourceId, mediaStream) {
    try {
      // Create media stream source
      const source = this.audioContext.createMediaStreamSource(mediaStream);

      // Create panner node for spatial positioning
      const panner = this.audioContext.createPanner();
      panner.panningModel = 'HRTF';
      panner.distanceModel = this.config.distanceModel;
      panner.refDistance = 1;
      panner.maxDistance = this.config.maxDistance;
      panner.rolloffFactor = this.config.rolloffFactor;
      panner.coneInnerAngle = this.config.coneInnerAngle;
      panner.coneOuterAngle = this.config.coneOuterAngle;
      panner.coneOuterGain = this.config.coneOuterGain;

      // Create gain nodes for processing
      const inputGain = this.audioContext.createGain();
      const distanceGain = this.audioContext.createGain();
      const effectsGain = this.audioContext.createGain();
      const outputGain = this.audioContext.createGain();

      // Create analyser for this source
      const analyser = this.audioContext.createAnalyser();
      analyser.fftSize = 128;

      // Create filters for character voice processing
      const filters = await this.createVoiceFilters();

      // Connect nodes: source -> input -> filters -> panner -> distance -> effects -> output -> master
      source.connect(inputGain);
      inputGain.connect(analyser);

      // Connect through filters
      let previousNode = analyser;
      filters.forEach(filter => {
        previousNode.connect(filter);
        previousNode = filter;
      });

      previousNode.connect(panner);
      panner.connect(distanceGain);
      distanceGain.connect(effectsGain);
      effectsGain.connect(outputGain);
      outputGain.connect(this.masterGain);

      // Create spatial source object
      const spatialSource = {
        id: sourceId,
        source,
        panner,
        inputGain,
        distanceGain,
        effectsGain,
        outputGain,
        analyser,
        filters,
        position: { x: 0, y: 0, z: 0 },
        velocity: { x: 0, y: 0, z: 0 },
        orientation: { x: 0, y: 0, z: 0 },
        isMuted: false,
        characterType: 'human',
        roomEffects: true
      };

      this.spatialSources.set(sourceId, spatialSource);
      this.metrics.activeSources++;

      // Start position tracking
      this.positionTracker.trackSource(sourceId, spatialSource);

      this.emit('spatialSourceCreated', { sourceId, spatialSource });

      return spatialSource;
    } catch (error) {
      console.error('Failed to create spatial source:', error);
      throw error;
    }
  }

  /**
   * Create voice filters for character processing
   */
  async createVoiceFilters() {
    const filters = [];

    // High-pass filter for character voice shaping
    const highPass = this.audioContext.createBiquadFilter();
    highPass.type = 'highpass';
    highPass.frequency.value = 80;
    highPass.Q.value = 1;
    filters.push(highPass);

    // Low-pass filter for smoothing
    const lowPass = this.audioContext.createBiquadFilter();
    lowPass.type = 'lowpass';
    lowPass.frequency.value = 8000;
    lowPass.Q.value = 1;
    filters.push(lowPass);

    // Peaking filter for character resonance
    const peak = this.audioContext.createBiquadFilter();
    peak.type = 'peaking';
    peak.frequency.value = 1000;
    peak.gain.value = 0;
    peak.Q.value = 1;
    filters.push(peak);

    return filters;
  }

  /**
   * Update source position for spatial audio
   */
  updateSourcePosition(sourceId, position) {
    if (!this.spatialSources.has(sourceId)) return;

    const source = this.spatialSources.get(sourceId);
    const oldPosition = { ...source.position };

    // Update position
    source.position = { ...position };

    // Calculate velocity for Doppler effect
    const deltaTime = 0.016; // ~60fps
    source.velocity = {
      x: (position.x - oldPosition.x) / deltaTime,
      y: (position.y - oldPosition.y) / deltaTime,
      z: (position.z - oldPosition.z) / deltaTime
    };

    // Update panner position
    source.panner.positionX.value = position.x;
    source.panner.positionY.value = position.y;
    source.panner.positionZ.value = position.z;

    // Update distance attenuation
    this.updateDistanceAttenuation(source);

    // Update Doppler effect
    this.updateDopplerEffect(source);

    this.emit('positionUpdate', { sourceId, position, velocity: source.velocity });
  }

  /**
   * Update source orientation
   */
  updateSourceOrientation(sourceId, orientation, direction) {
    if (!this.spatialSources.has(sourceId)) return;

    const source = this.spatialSources.get(sourceId);
    source.orientation = { ...orientation };

    // Update panner orientation
    source.panner.orientationX.value = direction.x;
    source.panner.orientationY.value = direction.y;
    source.panner.orientationZ.value = direction.z;
  }

  /**
   * Update distance attenuation based on position
   */
  updateDistanceAttenuation(source) {
    const listenerPos = this.listener.position;
    const distance = this.calculateDistance(source.position, {
      x: listenerPos.x,
      y: listenerPos.y,
      z: listenerPos.z
    });

    // Apply distance-based gain
    let gain = 1.0;

    switch (this.config.distanceModel) {
      case 'linear':
        gain = Math.max(0, 1 - (distance / this.config.maxDistance));
        break;
      case 'inverse':
        gain = 1 / (1 + this.config.rolloffFactor * distance);
        break;
      case 'exponential':
        gain = Math.pow(distance / this.config.refDistance, -this.config.rolloffFactor);
        break;
    }

    source.distanceGain.gain.value = gain;
  }

  /**
   * Update Doppler effect
   */
  updateDopplerEffect(source) {
    if (!this.config.dopplerFactor) return;

    const listenerPos = this.listener.position;
    const listenerVel = this.listener.velocity;

    // Calculate relative velocity
    const relativeVelocity = {
      x: source.velocity.x - listenerVel.x,
      y: source.velocity.y - listenerVel.y,
      z: source.velocity.z - listenerVel.z
    };

    // Calculate direction from source to listener
    const direction = {
      x: listenerPos.x - source.position.x,
      y: listenerPos.y - source.position.y,
      z: listenerPos.z - source.position.z
    };

    const distance = Math.sqrt(
      direction.x * direction.x +
      direction.y * direction.y +
      direction.z * direction.z
    );

    if (distance > 0) {
      // Normalize direction
      direction.x /= distance;
      direction.y /= distance;
      direction.z /= distance;

      // Calculate Doppler shift
      const relativeSpeed = (
        relativeVelocity.x * direction.x +
        relativeVelocity.y * direction.y +
        relativeVelocity.z * direction.z
      );

      const dopplerShift = 1 + (relativeSpeed / this.config.speedOfSound) * this.config.dopplerFactor;

      // Apply Doppler effect to panner
      if (source.panner.setVelocity) {
        source.panner.setVelocity(source.velocity.x, source.velocity.y, source.velocity.z);
      }
    }
  }

  /**
   * Apply character voice filter
   */
  applyCharacterFilter(sourceId, characterType) {
    if (!this.spatialSources.has(sourceId)) return;

    const source = this.spatialSources.get(sourceId);
    source.characterType = characterType;

    // Character-specific filter settings
    const characterFilters = {
      dwarvish: {
        highPassFreq: 60,
        lowPassFreq: 6000,
        peakFreq: 800,
        peakGain: 2,
        peakQ: 0.5
      },
      elvish: {
        highPassFreq: 100,
        lowPassFreq: 10000,
        peakFreq: 2000,
        peakGain: 1,
        peakQ: 1.5
      },
      orcish: {
        highPassFreq: 40,
        lowPassFreq: 4000,
        peakFreq: 400,
        peakGain: 4,
        peakQ: 0.3
      },
      draconic: {
        highPassFreq: 80,
        lowPassFreq: 12000,
        peakFreq: 1500,
        peakGain: 1.5,
        peakQ: 2
      },
      human: {
        highPassFreq: 80,
        lowPassFreq: 8000,
        peakFreq: 1000,
        peakGain: 0,
        peakQ: 1
      }
    };

    const filters = characterFilters[characterType] || characterFilters.human;

    // Apply filter settings
    if (source.filters[0]) { // High-pass
      source.filters[0].frequency.value = filters.highPassFreq;
    }
    if (source.filters[1]) { // Low-pass
      source.filters[1].frequency.value = filters.lowPassFreq;
    }
    if (source.filters[2]) { // Peak
      source.filters[2].frequency.value = filters.peakFreq;
      source.filters[2].gain.value = filters.peakGain;
      source.filters[2].Q.value = filters.peakQ;
    }

    this.emit('characterFilterApplied', { sourceId, characterType });
  }

  /**
   * Set listener position
   */
  setListenerPosition(position) {
    this.listener.positionX.value = position.x;
    this.listener.positionY.value = position.y;
    this.listener.positionZ.value = position.z;

    // Update all sources for distance attenuation
    for (const [sourceId, source] of this.spatialSources) {
      this.updateDistanceAttenuation(source);
    }

    this.emit('listenerPositionUpdate', position);
  }

  /**
   * Set listener orientation
   */
  setListenerOrientation(forward, up) {
    this.listener.forwardX.value = forward.x;
    this.listener.forwardY.value = forward.y;
    this.listener.forwardZ.value = forward.z;

    this.listener.upX.value = up.x;
    this.listener.upY.value = up.y;
    this.listener.upZ.value = up.z;

    this.emit('listenerOrientationUpdate', { forward, up });
  }

  /**
   * Set room size and acoustics
   */
  setRoomSize(roomSize) {
    this.roomAcoustics.setRoomSize(roomSize);

    // Apply room effects to all sources
    for (const [sourceId, source] of this.spatialSources) {
      if (source.roomEffects) {
        this.applyRoomAcoustics(source);
      }
    }

    this.emit('roomSizeChanged', { roomSize });
  }

  /**
   * Apply room acoustics to a source
   */
  applyRoomAcoustics(source) {
    const listenerPos = this.listener.position;
    const distance = this.calculateDistance(source.position, {
      x: listenerPos.x,
      y: listenerPos.y,
      z: listenerPos.z
    });

    const roomResponse = this.roomAcoustics.getRoomResponse(distance, source.position);

    // Apply room response to effects gain
    source.effectsGain.gain.value = roomResponse.reverbLevel;
  }

  /**
   * Apply environmental audio effects
   */
  applyEnvironmentalEffect(sourceId, effectType, intensity = 1.0) {
    if (!this.spatialSources.has(sourceId)) return;

    const source = this.spatialSources.get(sourceId);
    this.environmentalEffects.applyEffect(source, effectType, intensity);

    this.emit('environmentalEffectApplied', { sourceId, effectType, intensity });
  }

  /**
   * Calculate distance between two points
   */
  calculateDistance(pos1, pos2) {
    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    const dz = pos1.z - pos2.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /**
   * Mute/unmute a spatial source
   */
  muteSource(sourceId, mute = true) {
    if (!this.spatialSources.has(sourceId)) return;

    const source = this.spatialSources.get(sourceId);
    source.isMuted = mute;
    source.outputGain.gain.value = mute ? 0 : 1;

    this.emit('sourceMuted', { sourceId, muted: mute });
  }

  /**
   * Set source volume
   */
  setSourceVolume(sourceId, volume) {
    if (!this.spatialSources.has(sourceId)) return;

    const source = this.spatialSources.get(sourceId);
    source.outputGain.gain.value = Math.max(0, Math.min(1, volume));

    this.emit('sourceVolumeChanged', { sourceId, volume });
  }

  /**
   * Get source audio levels
   */
  getSourceLevels(sourceId) {
    if (!this.spatialSources.has(sourceId)) return null;

    const source = this.spatialSources.get(sourceId);
    const dataArray = new Uint8Array(source.analyser.frequencyBinCount);
    source.analyser.getByteFrequencyData(dataArray);

    // Calculate RMS and peak levels
    let sum = 0;
    let peak = 0;
    for (let i = 0; i < dataArray.length; i++) {
      const value = dataArray[i] / 255;
      sum += value * value;
      peak = Math.max(peak, value);
    }

    const rms = Math.sqrt(sum / dataArray.length);

    return {
      rms,
      peak,
      frequencyData: Array.from(dataArray)
    };
  }

  /**
   * Get overall audio levels
   */
  getOverallLevels() {
    const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    this.analyser.getByteFrequencyData(dataArray);

    let sum = 0;
    let peak = 0;
    for (let i = 0; i < dataArray.length; i++) {
      const value = dataArray[i] / 255;
      sum += value * value;
      peak = Math.max(peak, value);
    }

    const rms = Math.sqrt(sum / dataArray.length);

    return {
      rms,
      peak,
      frequencyData: Array.from(dataArray),
      activeSources: this.spatialSources.size
    };
  }

  /**
   * Update global configuration
   */
  updateConfig(newConfig) {
    this.config = { ...this.config, ...newConfig };

    // Update existing panners with new settings
    for (const [sourceId, source] of this.spatialSources) {
      source.panner.distanceModel = this.config.distanceModel;
      source.panner.maxDistance = this.config.maxDistance;
      source.panner.rolloffFactor = this.config.rolloffFactor;
      source.panner.coneInnerAngle = this.config.coneInnerAngle;
      source.panner.coneOuterAngle = this.config.coneOuterAngle;
      source.panner.coneOuterGain = this.config.coneOuterGain;

      this.updateDistanceAttenuation(source);
    }

    this.emit('configUpdated', this.config);
  }

  /**
   * Remove spatial source
   */
  removeSpatialSource(sourceId) {
    if (!this.spatialSources.has(sourceId)) return;

    const source = this.spatialSources.get(sourceId);

    // Disconnect all nodes
    source.source.disconnect();
    source.inputGain.disconnect();
    source.filters.forEach(filter => filter.disconnect());
    source.panner.disconnect();
    source.distanceGain.disconnect();
    source.effectsGain.disconnect();
    source.outputGain.disconnect();
    source.analyser.disconnect();

    // Remove from tracking
    this.positionTracker.untrackSource(sourceId);

    // Remove from sources
    this.spatialSources.delete(sourceId);
    this.metrics.activeSources--;

    this.emit('spatialSourceRemoved', { sourceId });
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
          console.error(`Error in spatial audio event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Get performance metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      sources: this.spatialSources.size,
      audioContextState: this.audioContext.state,
      currentTime: this.audioContext.currentTime
    };
  }

  /**
   * Cleanup and destroy the spatial audio engine
   */
  cleanup() {
    // Remove all sources
    for (const [sourceId] of this.spatialSources) {
      this.removeSpatialSource(sourceId);
    }

    // Cleanup components
    this.roomAcoustics.cleanup();
    this.environmentalEffects.cleanup();
    this.positionTracker.cleanup();

    // Disconnect master gain
    this.masterGain.disconnect();

    // Clear event listeners
    this.eventListeners.clear();
    this.workletProcessors.clear();

    this.emit('cleanupComplete');
  }
}