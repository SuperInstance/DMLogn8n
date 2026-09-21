/**
 * Room Acoustics Simulator - Simulates realistic room acoustics and reverberation
 * Provides different room sizes and acoustic properties for immersive audio
 */

export class RoomAcousticsSimulator {
  constructor(audioContext, roomSize = 'medium') {
    this.audioContext = audioContext;
    this.currentRoomSize = roomSize;

    // Room presets with acoustic properties
    this.roomPresets = {
      small: {
        dimensions: { width: 5, height: 3, length: 5 }, // meters
        reverbTime: 0.8, // seconds
        damping: 0.7,
        earlyReflections: 0.3,
        lateReflections: 0.2,
        airAbsorption: 0.98
      },
      medium: {
        dimensions: { width: 10, height: 4, length: 10 },
        reverbTime: 1.5,
        damping: 0.5,
        earlyReflections: 0.5,
        lateReflections: 0.4,
        airAbsorption: 0.95
      },
      large: {
        dimensions: { width: 20, height: 6, length: 20 },
        reverbTime: 2.5,
        damping: 0.3,
        earlyReflections: 0.6,
        lateReflections: 0.6,
        airAbsorption: 0.90
      },
      hall: {
        dimensions: { width: 30, height: 10, length: 40 },
        reverbTime: 3.5,
        damping: 0.2,
        earlyReflections: 0.7,
        lateReflections: 0.8,
        airAbsorption: 0.85
      },
      cave: {
        dimensions: { width: 15, height: 8, length: 25 },
        reverbTime: 4.0,
        damping: 0.1,
        earlyReflections: 0.4,
        lateReflections: 0.9,
        airAbsorption: 0.88
      },
      forest: {
        dimensions: { width: 50, height: 20, length: 50 },
        reverbTime: 1.0,
        damping: 0.8,
        earlyReflections: 0.2,
        lateReflections: 0.1,
        airAbsorption: 0.92
      }
    };

    // Convolution reverb setup
    this.convolverNodes = new Map();
    this.impulseResponses = new Map();

    // Multi-tap delay for early reflections
    this.delayNodes = new Map();

    // Filter nodes for frequency-dependent absorption
    this.filterNodes = new Map();

    // Current room properties
    this.roomProperties = this.roomPresets[roomSize];

    // Initialize audio nodes
    this.initializeAudioNodes();
  }

  /**
   * Initialize the room acoustics system
   */
  async initialize() {
    try {
      // Generate impulse responses for different room sizes
      await this.generateImpulseResponses();

      // Initialize convolution reverbs
      await this.initializeConvolutionReverbs();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize room acoustics:', error);
      throw error;
    }
  }

  /**
   * Initialize audio processing nodes
   */
  initializeAudioNodes() {
    // Create master reverb send
    this.reverbMasterGain = this.audioContext.createGain();
    this.reverbMasterGain.gain.value = 0.3;

    // Create early reflection send
    this.earlyReflectionGain = this.audioContext.createGain();
    this.earlyReflectionGain.gain.value = 0.2;

    // Connect to destination
    this.reverbMasterGain.connect(this.audioContext.destination);
    this.earlyReflectionGain.connect(this.audioContext.destination);
  }

  /**
   * Generate impulse responses for convolution reverb
   */
  async generateImpulseResponses() {
    for (const [roomType, preset] of Object.entries(this.roomPresets)) {
      const impulseResponse = await this.createImpulseResponse(preset);
      this.impulseResponses.set(roomType, impulseResponse);
    }
  }

  /**
   * Create impulse response for a room preset
   */
  async createImpulseResponse(roomPreset) {
    const sampleRate = this.audioContext.sampleRate;
    const length = Math.floor(roomPreset.reverbTime * sampleRate);
    const impulseResponse = this.audioContext.createBuffer(2, length, sampleRate);

    // Generate impulse response with exponential decay
    for (let channel = 0; channel < 2; channel++) {
      const channelData = impulseResponse.getChannelData(channel);

      for (let i = 0; i < length; i++) {
        const time = i / sampleRate;

        // Exponential decay with room damping
        const decay = Math.exp(-time / (roomPreset.reverbTime * roomPreset.damping));

        // Add some randomness for natural sound
        const noise = (Math.random() - 0.5) * 0.02;

        // Apply frequency-dependent absorption
        const frequencyResponse = this.calculateFrequencyResponse(time, roomPreset);

        channelData[i] = decay * (1 + noise) * frequencyResponse;
      }
    }

    return impulseResponse;
  }

  /**
   * Calculate frequency response for realistic acoustics
   */
  calculateFrequencyResponse(time, roomPreset) {
    // High frequencies absorb faster
    const highFrequencyAbsorption = Math.exp(-time * 0.5);

    // Low frequencies linger longer
    const lowFrequencyBoost = Math.exp(-time * 0.1);

    return (highFrequencyAbsorption + lowFrequencyBoost) / 2 * roomPreset.airAbsorption;
  }

  /**
   * Initialize convolution reverb nodes
   */
  async initializeConvolutionReverbs() {
    for (const [roomType, impulseResponse] of this.impulseResponses) {
      const convolver = this.audioContext.createConvolver();
      convolver.buffer = impulseResponse;

      // Create wet/dry mix control
      const wetGain = this.audioContext.createGain();
      const dryGain = this.audioContext.createGain();
      const merger = this.audioContext.createChannelMerger(2);

      wetGain.gain.value = roomPresets[roomType].lateReflections;
      dryGain.gain.value = 1 - roomPresets[roomType].lateReflections;

      this.convolverNodes.set(roomType, {
        convolver,
        wetGain,
        dryGain,
        merger
      });
    }
  }

  /**
   * Set room size
   */
  setRoomSize(roomSize) {
    if (!this.roomPresets[roomSize]) {
      console.warn(`Unknown room size: ${roomSize}`);
      return;
    }

    this.currentRoomSize = roomSize;
    this.roomProperties = this.roomPresets[roomSize];

    this.emit('roomSizeChanged', { roomSize, properties: this.roomProperties });
  }

  /**
   * Get room response for a position
   */
  getRoomResponse(distance, position) {
    const response = {
      directSound: this.calculateDirectSound(distance),
      earlyReflections: this.calculateEarlyReflections(distance, position),
      lateReflections: this.calculateLateReflections(distance),
      airAbsorption: this.calculateAirAbsorption(distance),
      obstructionEffect: this.calculateObstructionEffect(position)
    };

    return response;
  }

  /**
   * Calculate direct sound attenuation
   */
  calculateDirectSound(distance) {
    // Inverse square law for direct sound
    const attenuation = 1 / (1 + distance * 0.1);
    return Math.max(0, attenuation);
  }

  /**
   * Calculate early reflections
   */
  calculateEarlyReflections(distance, position) {
    // Early reflections depend on distance and room geometry
    const earlyReflectionDelay = distance / 343; // Speed of sound in m/s
    const earlyReflectionLevel = this.roomProperties.earlyReflections * Math.exp(-distance * 0.05);

    return {
      delay: earlyReflectionDelay,
      level: earlyReflectionLevel,
      pattern: this.calculateReflectionPattern(position)
    };
  }

  /**
   * Calculate late reflections (reverberation)
   */
  calculateLateReflections(distance) {
    // Late reflections create the sense of space
    const reverbLevel = this.roomProperties.lateReflections * Math.exp(-distance * 0.02);
    const reverbTime = this.roomProperties.reverbTime;

    return {
      level: reverbLevel,
      decayTime: reverbTime,
      damping: this.roomProperties.damping
    };
  }

  /**
   * Calculate air absorption
   */
  calculateAirAbsorption(distance) {
    // High frequencies are absorbed more by air
    const airAbsorptionFactor = this.roomProperties.airAbsorption;
    const distanceAttenuation = Math.pow(airAbsorptionFactor, distance / 10);

    return distanceAttenuation;
  }

  /**
   * Calculate obstruction effect
   */
  calculateObstructionEffect(position) {
    // Simple obstruction simulation (can be enhanced with ray tracing)
    const obstruction = 1.0; // No obstruction by default
    return obstruction;
  }

  /**
   * Calculate reflection pattern based on position
   */
  calculateReflectionPattern(position) {
    const pattern = [];

    // Calculate reflections from walls, floor, and ceiling
    const { dimensions } = this.roomProperties;

    // Wall reflections
    pattern.push(
      this.calculateWallReflection(position, { x: 0, y: 0, z: 1 }, dimensions.length / 2),
      this.calculateWallReflection(position, { x: 0, y: 0, z: -1 }, dimensions.length / 2),
      this.calculateWallReflection(position, { x: 1, y: 0, z: 0 }, dimensions.width / 2),
      this.calculateWallReflection(position, { x: -1, y: 0, z: 0 }, dimensions.width / 2)
    );

    // Floor and ceiling reflections
    pattern.push(
      this.calculateWallReflection(position, { x: 0, y: -1, z: 0 }, dimensions.height / 2),
      this.calculateWallReflection(position, { x: 0, y: 1, z: 0 }, dimensions.height / 2)
    );

    return pattern.filter(reflection => reflection.level > 0.01);
  }

  /**
   * Calculate single wall reflection
   */
  calculateWallReflection(position, normal, distance) {
    const dotProduct = position.x * normal.x + position.y * normal.y + position.z * normal.z;
    const reflectionDistance = Math.abs(distance - dotProduct);
    const reflectionDelay = reflectionDistance / 343;
    const reflectionLevel = Math.exp(-reflectionDistance * 0.1) * 0.3;

    return {
      delay: reflectionDelay,
      level: reflectionLevel,
      direction: normal
    };
  }

  /**
   * Apply room acoustics to an audio node
   */
  applyRoomAcoustics(sourceNode, sourceId, position) {
    const distance = this.calculateDistance(position, { x: 0, y: 0, z: 0 });
    const roomResponse = this.getRoomResponse(distance, position);

    // Create audio processing chain for room acoustics
    const inputGain = this.audioContext.createGain();
    const directGain = this.audioContext.createGain();
    const reverbGain = this.audioContext.createGain();
    const earlyGain = this.audioContext.createGain();
    const outputMerger = this.audioContext.createChannelMerger(2);

    // Set gain values based on room response
    directGain.gain.value = roomResponse.directSound;
    reverbGain.gain.value = roomResponse.lateReflections.level;
    earlyGain.gain.value = roomResponse.earlyReflections.level;

    // Connect direct path
    sourceNode.connect(inputGain);
    inputGain.connect(directGain);
    directGain.connect(outputMerger, 0, 0);
    directGain.connect(outputMerger, 0, 1);

    // Connect to reverb
    const reverbNode = this.convolverNodes.get(this.currentRoomSize);
    if (reverbNode) {
      inputGain.connect(reverbGain);
      reverbGain.connect(reverbNode.convolver);
      reverbNode.convolver.connect(reverbNode.wetGain);
      reverbNode.wetGain.connect(outputMerger, 0, 0);
      reverbNode.wetGain.connect(outputMerger, 0, 1);
    }

    // Connect early reflections
    this.createEarlyReflections(inputGain, earlyGain, roomResponse.earlyReflections);

    return {
      inputGain,
      directGain,
      reverbGain,
      earlyGain,
      outputMerger
    };
  }

  /**
   * Create early reflection delays
   */
  createEarlyReflections(inputNode, gainNode, earlyReflections) {
    const pattern = earlyReflections.pattern || [];

    pattern.forEach((reflection, index) => {
      const delay = this.audioContext.createDelay(5.0);
      const reflectionGain = this.audioContext.createGain();

      delay.delayTime.value = reflection.delay;
      reflectionGain.gain.value = reflection.level;

      inputNode.connect(delay);
      delay.connect(reflectionGain);
      reflectionGain.connect(gainNode);
    });
  }

  /**
   * Calculate distance between two positions
   */
  calculateDistance(pos1, pos2) {
    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    const dz = pos1.z - pos2.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  /**
   * Create custom room preset
   */
  createCustomRoomPreset(name, properties) {
    this.roomPresets[name] = {
      dimensions: properties.dimensions || { width: 10, height: 4, length: 10 },
      reverbTime: properties.reverbTime || 1.5,
      damping: properties.damping || 0.5,
      earlyReflections: properties.earlyReflections || 0.5,
      lateReflections: properties.lateReflections || 0.4,
      airAbsorption: properties.airAbsorption || 0.95
    };

    // Generate impulse response for the new preset
    this.createImpulseResponse(this.roomPresets[name])
      .then(impulseResponse => {
        this.impulseResponses.set(name, impulseResponse);
        this.initializeConvolutionReverbs();
      });
  }

  /**
   * Get current room properties
   */
  getCurrentRoomProperties() {
    return {
      roomSize: this.currentRoomSize,
      properties: { ...this.roomProperties }
    };
  }

  /**
   * Event emitter methods
   */
  on(event, callback) {
    if (!this.eventListeners) {
      this.eventListeners = new Map();
    }
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  emit(event, data) {
    if (this.eventListeners && this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in room acoustics event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup and destroy the room acoustics simulator
   */
  cleanup() {
    // Disconnect all convolver nodes
    for (const [roomType, convolverNodes] of this.convolverNodes) {
      convolverNodes.convolver.disconnect();
      convolverNodes.wetGain.disconnect();
      convolverNodes.dryGain.disconnect();
      convolverNodes.merger.disconnect();
    }

    // Clear all references
    this.convolverNodes.clear();
    this.impulseResponses.clear();
    this.delayNodes.clear();
    this.filterNodes.clear();

    // Disconnect master nodes
    if (this.reverbMasterGain) {
      this.reverbMasterGain.disconnect();
    }
    if (this.earlyReflectionGain) {
      this.earlyReflectionGain.disconnect();
    }

    if (this.eventListeners) {
      this.eventListeners.clear();
    }
  }
}