/**
 * Environmental Audio Effects - Provides dynamic environmental audio processing
 * Includes weather effects, terrain-based audio, and atmospheric conditions
 */

export class EnvironmentalAudioEffects {
  constructor(audioContext) {
    this.audioContext = audioContext;

    // Environmental effect processors
    this.effectProcessors = new Map();

    // Weather and environmental conditions
    this.currentConditions = {
      weather: 'clear',
      terrain: 'indoor',
      timeOfDay: 'day',
      temperature: 20, // Celsius
      humidity: 50, // Percentage
      windSpeed: 0, // m/s
      precipitation: 0 // mm/hour
    };

    // Effect parameters
    this.effectParameters = {
      rain: {
        intensity: 0,
        frequency: 1000,
        bandwidth: 500,
        volume: 0.3
      },
      wind: {
        intensity: 0,
        frequency: 200,
        modulation: 0.5,
        volume: 0.2
      },
      thunder: {
        intensity: 0,
        lowFreqGain: 0.8,
        duration: 2.0,
        volume: 0.6
      },
      echo: {
        delay: 0.3,
        feedback: 0.4,
        filter: 0.7
      },
      underwater: {
        lowPassFreq: 800,
        damping: 0.9,
        bubbles: true
      },
      fire: {
        crackleIntensity: 0.5,
        lowFreqContent: 0.7,
        volume: 0.4
      }
    };

    // Ambient sound generators
    this.ambientGenerators = new Map();

    // Event system
    this.eventListeners = new Map();
  }

  /**
   * Initialize the environmental audio effects system
   */
  async initialize() {
    try {
      // Load audio worklets for advanced processing
      await this.loadEnvironmentalWorklets();

      // Initialize ambient sound generators
      await this.initializeAmbientGenerators();

      // Create effect processing chains
      await this.createEffectProcessors();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize environmental audio effects:', error);
      throw error;
    }
  }

  /**
   * Load environmental audio worklets
   */
  async loadEnvironmentalWorklets() {
    const worklets = [
      'rain-processor.js',
      'wind-processor.js',
      'thunder-processor.js',
      'underwater-processor.js'
    ];

    for (const worklet of worklets) {
      try {
        await this.audioContext.audioWorklet.addModule(`/worklets/${worklet}`);
      } catch (error) {
        console.warn(`Failed to load environmental worklet ${worklet}:`, error);
      }
    }
  }

  /**
   * Initialize ambient sound generators
   */
  async initializeAmbientGenerators() {
    // Rain generator
    const rainGenerator = this.createRainGenerator();
    this.ambientGenerators.set('rain', rainGenerator);

    // Wind generator
    const windGenerator = this.createWindGenerator();
    this.ambientGenerators.set('wind', windGenerator);

    // Thunder generator
    const thunderGenerator = this.createThunderGenerator();
    this.ambientGenerators.set('thunder', thunderGenerator);

    // Fire generator
    const fireGenerator = this.createFireGenerator();
    this.ambientGenerators.set('fire', fireGenerator);

    // Underwater bubbles generator
    const bubbleGenerator = this.createBubbleGenerator();
    this.ambientGenerators.set('bubbles', bubbleGenerator);
  }

  /**
   * Create rain sound generator
   */
  createRainGenerator() {
    const bufferSize = 4096;
    const noiseBuffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
    const noiseData = noiseBuffer.getChannelData(0);

    // Generate white noise
    for (let i = 0; i < bufferSize; i++) {
      noiseData[i] = (Math.random() - 0.5) * 2;
    }

    const noiseSource = this.audioContext.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    // Create rain processing chain
    const highPass = this.audioContext.createBiquadFilter();
    highPass.type = 'highpass';
    highPass.frequency.value = this.effectParameters.rain.frequency;

    const bandPass = this.audioContext.createBiquadFilter();
    bandPass.type = 'bandpass';
    bandPass.frequency.value = this.effectParameters.rain.frequency;
    bandPass.Q.value = 2;

    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = 0;

    // Connect nodes
    noiseSource.connect(highPass);
    highPass.connect(bandPass);
    bandPass.connect(gainNode);

    // Start the noise source
    noiseSource.start();

    return {
      source: noiseSource,
      highPass,
      bandPass,
      gain: gainNode,
      type: 'rain'
    };
  }

  /**
   * Create wind sound generator
   */
  createWindGenerator() {
    const bufferSize = 8192;
    const noiseBuffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
    const noiseData = noiseBuffer.getChannelData(0);

    // Generate pink noise for more realistic wind
    for (let i = 0; i < bufferSize; i++) {
      noiseData[i] = (Math.random() - 0.5) * 2 / (i + 1);
    }

    const noiseSource = this.audioContext.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    // Create wind processing chain
    const lowPass = this.audioContext.createBiquadFilter();
    lowPass.type = 'lowpass';
    lowPass.frequency.value = this.effectParameters.wind.frequency;

    const lfo = this.audioContext.createOscillator();
    lfo.frequency.value = 0.2; // Slow modulation

    const lfoGain = this.audioContext.createGain();
    lfoGain.gain.value = 200;

    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = 0;

    // Connect LFO to filter frequency for wind gusts
    lfo.connect(lfoGain);
    lfoGain.connect(lowPass.frequency);

    // Connect main audio chain
    noiseSource.connect(lowPass);
    lowPass.connect(gainNode);

    // Start the sources
    noiseSource.start();
    lfo.start();

    return {
      source: noiseSource,
      lfo,
      lowPass,
      lfoGain,
      gain: gainNode,
      type: 'wind'
    };
  }

  /**
   * Create thunder sound generator
   */
  createThunderGenerator() {
    const thunderGenerator = {
      isPlaying: false,
      currentThunder: null,
      type: 'thunder',

      play: (intensity = 0.5) => {
        if (thunderGenerator.isPlaying) return;

        thunderGenerator.isPlaying = true;

        // Create thunder buffer with low frequency rumble
        const duration = 1 + Math.random() * 3; // 1-4 seconds
        const bufferSize = duration * this.audioContext.sampleRate;
        const thunderBuffer = this.audioContext.createBuffer(2, bufferSize, this.audioContext.sampleRate);

        for (let channel = 0; channel < 2; channel++) {
          const channelData = thunderBuffer.getChannelData(channel);

          for (let i = 0; i < bufferSize; i++) {
            const time = i / this.audioContext.sampleRate;

            // Create low frequency rumble with decay
            const decay = Math.exp(-time * 2);
            const noise = (Math.random() - 0.5) * intensity * decay;
            const lowFreq = Math.sin(2 * Math.PI * 50 * time) * decay * 0.5;

            channelData[i] = noise + lowFreq;
          }
        }

        const thunderSource = this.audioContext.createBufferSource();
        thunderSource.buffer = thunderBuffer;

        const gainNode = this.audioContext.createGain();
        gainNode.gain.value = intensity * this.effectParameters.thunder.volume;

        const lowPass = this.audioContext.createBiquadFilter();
        lowPass.type = 'lowpass';
        lowPass.frequency.value = 200;

        // Connect and play
        thunderSource.connect(lowPass);
        lowPass.connect(gainNode);
        gainNode.connect(this.audioContext.destination);

        thunderSource.start();
        thunderGenerator.currentThunder = thunderSource;

        thunderSource.onended = () => {
          thunderGenerator.isPlaying = false;
          thunderGenerator.currentThunder = null;
        };
      }
    };

    return thunderGenerator;
  }

  /**
   * Create fire sound generator
   */
  createFireGenerator() {
    const bufferSize = 2048;
    const noiseBuffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
    const noiseData = noiseBuffer.getChannelData(0);

    // Generate crackling noise
    for (let i = 0; i < bufferSize; i++) {
      noiseData[i] = Math.random() > 0.95 ? (Math.random() - 0.5) * 2 : 0;
    }

    const noiseSource = this.audioContext.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    // Create fire processing chain
    const highPass = this.audioContext.createBiquadFilter();
    highPass.type = 'highpass';
    highPass.frequency.value = 300;

    const lowPass = this.audioContext.createBiquadFilter();
    lowPass.type = 'lowpass';
    lowPass.frequency.value = 3000;

    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = 0;

    // Create LFO for flickering effect
    const lfo = this.audioContext.createOscillator();
    lfo.frequency.value = 8 + Math.random() * 4; // 8-12 Hz flicker

    const lfoGain = this.audioContext.createGain();
    lfoGain.gain.value = 0.3;

    lfo.connect(lfoGain);
    lfoGain.connect(gainNode.gain);

    // Connect main chain
    noiseSource.connect(highPass);
    highPass.connect(lowPass);
    lowPass.connect(gainNode);

    // Start sources
    noiseSource.start();
    lfo.start();

    return {
      source: noiseSource,
      lfo,
      highPass,
      lowPass,
      lfoGain,
      gain: gainNode,
      type: 'fire'
    };
  }

  /**
   * Create underwater bubble generator
   */
  createBubbleGenerator() {
    const bubbleGenerator = {
      isPlaying: false,
      sources: [],
      type: 'bubbles',

      start: () => {
        if (bubbleGenerator.isPlaying) return;

        bubbleGenerator.isPlaying = true;
        bubbleGenerator.generateBubbles();
      },

      stop: () => {
        bubbleGenerator.isPlaying = false;
        bubbleGenerator.sources.forEach(source => {
          source.source.stop();
          source.gain.disconnect();
        });
        bubbleGenerator.sources = [];
      },

      generateBubbles: () => {
        if (!bubbleGenerator.isPlaying) return;

        // Create random bubble
        const bubbleSource = this.audioContext.createOscillator();
        bubbleSource.frequency.value = 200 + Math.random() * 800;

        const bubbleGain = this.audioContext.createGain();

        // Bubble envelope
        const now = this.audioContext.currentTime;
        bubbleGain.gain.setValueAtTime(0, now);
        bubbleGain.gain.linearRampToValueAtTime(0.1, now + 0.01);
        bubbleGain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);

        bubbleSource.connect(bubbleGain);
        bubbleGain.connect(this.audioContext.destination);

        bubbleSource.start(now);
        bubbleSource.stop(now + 0.1);

        const bubbleData = { source: bubbleSource, gain: bubbleGain };
        bubbleGenerator.sources.push(bubbleData);

        // Clean up finished bubbles
        setTimeout(() => {
          const index = bubbleGenerator.sources.indexOf(bubbleData);
          if (index > -1) {
            bubbleGenerator.sources.splice(index, 1);
          }
        }, 200);

        // Schedule next bubble
        const nextBubbleTime = 100 + Math.random() * 500; // 100-600ms
        setTimeout(() => bubbleGenerator.generateBubbles(), nextBubbleTime);
      }
    };

    return bubbleGenerator;
  }

  /**
   * Create effect processing chains
   */
  async createEffectProcessors() {
    // Rain effect processor
    this.effectProcessors.set('rain', {
      generator: this.ambientGenerators.get('rain'),
      intensity: 0,
      active: false
    });

    // Wind effect processor
    this.effectProcessors.set('wind', {
      generator: this.ambientGenerators.get('wind'),
      intensity: 0,
      active: false
    });

    // Thunder effect processor
    this.effectProcessors.set('thunder', {
      generator: this.ambientGenerators.get('thunder'),
      intensity: 0,
      active: false
    });

    // Fire effect processor
    this.effectProcessors.set('fire', {
      generator: this.ambientGenerators.get('fire'),
      intensity: 0,
      active: false
    });

    // Underwater effect processor
    this.effectProcessors.set('underwater', {
      createFilterChain: () => {
        const lowPass = this.audioContext.createBiquadFilter();
        lowPass.type = 'lowpass';
        lowPass.frequency.value = this.effectParameters.underwater.lowPassFreq;
        lowPass.Q.value = 1;

        const compressor = this.audioContext.createDynamicsCompressor();
        compressor.threshold.value = -24;
        compressor.knee.value = 8;
        compressor.ratio.value = 4;
        compressor.attack.value = 0.01;
        compressor.release.value = 0.25;

        return { lowPass, compressor };
      },
      intensity: 0,
      active: false
    });
  }

  /**
   * Apply environmental effect to a source
   */
  applyEffect(source, effectType, intensity = 1.0) {
    const processor = this.effectProcessors.get(effectType);
    if (!processor) return;

    processor.intensity = Math.max(0, Math.min(1, intensity));
    processor.active = processor.intensity > 0;

    switch (effectType) {
      case 'rain':
        this.applyRainEffect(processor, intensity);
        break;
      case 'wind':
        this.applyWindEffect(processor, intensity);
        break;
      case 'thunder':
        this.applyThunderEffect(processor, intensity);
        break;
      case 'fire':
        this.applyFireEffect(processor, intensity);
        break;
      case 'underwater':
        this.applyUnderwaterEffect(source, processor, intensity);
        break;
      case 'echo':
        this.applyEchoEffect(source, processor, intensity);
        break;
    }

    this.emit('effectApplied', { effectType, intensity, source });
  }

  /**
   * Apply rain effect
   */
  applyRainEffect(processor, intensity) {
    const generator = processor.generator;
    if (!generator) return;

    generator.gain.gain.value = intensity * this.effectParameters.rain.volume;
    generator.highPass.frequency.value = 800 + intensity * 400;
    generator.bandPass.frequency.value = 1000 + intensity * 500;

    if (intensity > 0 && !processor.active) {
      generator.gain.connect(this.audioContext.destination);
    } else if (intensity === 0 && processor.active) {
      generator.gain.disconnect();
    }
  }

  /**
   * Apply wind effect
   */
  applyWindEffect(processor, intensity) {
    const generator = processor.generator;
    if (!generator) return;

    generator.gain.gain.value = intensity * this.effectParameters.wind.volume;
    generator.lowPass.frequency.value = 100 + intensity * 300;
    generator.lfo.frequency.value = 0.1 + intensity * 2;
    generator.lfoGain.gain.value = intensity * 200;

    if (intensity > 0 && !processor.active) {
      generator.gain.connect(this.audioContext.destination);
    } else if (intensity === 0 && processor.active) {
      generator.gain.disconnect();
    }
  }

  /**
   * Apply thunder effect
   */
  applyThunderEffect(processor, intensity) {
    const generator = processor.generator;
    if (!generator) return;

    processor.intensity = intensity;

    if (intensity > 0 && !processor.active) {
      // Schedule random thunder strikes
      const scheduleThunder = () => {
        if (processor.intensity === 0) return;

        generator.play(processor.intensity);

        // Schedule next thunder based on intensity
        const nextStrike = 2000 / intensity + Math.random() * 5000;
        setTimeout(scheduleThunder, nextStrike);
      };

      scheduleThunder();
    }
  }

  /**
   * Apply fire effect
   */
  applyFireEffect(processor, intensity) {
    const generator = processor.generator;
    if (!generator) return;

    generator.gain.gain.value = intensity * this.effectParameters.fire.volume;
    generator.highPass.frequency.value = 200 + intensity * 200;
    generator.lowPass.frequency.value = 2000 + intensity * 1000;
    generator.lfo.frequency.value = 5 + intensity * 10;

    if (intensity > 0 && !processor.active) {
      generator.gain.connect(this.audioContext.destination);
    } else if (intensity === 0 && processor.active) {
      generator.gain.disconnect();
    }
  }

  /**
   * Apply underwater effect
   */
  applyUnderwaterEffect(source, processor, intensity) {
    const filterChain = processor.createFilterChain();

    // Disconnect existing connections and insert filters
    const originalConnections = [];

    // Store original connections and insert underwater filters
    if (source.outputGain) {
      source.outputGain.disconnect();
      source.outputGain.connect(filterChain.lowPass);
      filterChain.lowPass.connect(filterChain.compressor);
      filterChain.compressor.connect(this.audioContext.destination);
    }

    // Start bubble generator if intensity is high enough
    const bubbleGenerator = this.ambientGenerators.get('bubbles');
    if (intensity > 0.3 && bubbleGenerator) {
      bubbleGenerator.start();
    } else if (bubbleGenerator) {
      bubbleGenerator.stop();
    }

    processor.filterChain = filterChain;
  }

  /**
   * Apply echo effect
   */
  applyEchoEffect(source, processor, intensity) {
    if (!source) return;

    // Create delay and feedback nodes
    const delay = this.audioContext.createDelay(2.0);
    const feedback = this.audioContext.createGain();
    const wetGain = this.audioContext.createGain();

    delay.delayTime.value = this.effectParameters.echo.delay * (1 + intensity);
    feedback.gain.value = this.effectParameters.echo.feedback * intensity;
    wetGain.gain.value = intensity * 0.5;

    // Create filter for echo
    const echoFilter = this.audioContext.createBiquadFilter();
    echoFilter.type = 'lowpass';
    echoFilter.frequency.value = 2000 * this.effectParameters.echo.filter;

    // Connect echo chain
    if (source.outputGain) {
      source.outputGain.connect(delay);
      delay.connect(feedback);
      feedback.connect(delay); // Feedback loop
      delay.connect(echoFilter);
      echoFilter.connect(wetGain);
      wetGain.connect(this.audioContext.destination);
    }

    processor.echoChain = { delay, feedback, wetGain, echoFilter };
  }

  /**
   * Set weather conditions
   */
  setWeatherConditions(weather, intensity = 0.5) {
    this.currentConditions.weather = weather;

    switch (weather) {
      case 'rain':
        this.applyEffect(null, 'rain', intensity);
        if (intensity > 0.7) {
          this.applyEffect(null, 'thunder', intensity * 0.5);
        }
        break;
      case 'wind':
        this.applyEffect(null, 'wind', intensity);
        break;
      case 'storm':
        this.applyEffect(null, 'rain', intensity);
        this.applyEffect(null, 'wind', intensity * 0.8);
        this.applyEffect(null, 'thunder', intensity * 0.7);
        break;
      case 'clear':
        this.applyEffect(null, 'rain', 0);
        this.applyEffect(null, 'wind', 0);
        this.applyEffect(null, 'thunder', 0);
        break;
    }

    this.emit('weatherChanged', { weather, intensity });
  }

  /**
   * Set terrain type
   */
  setTerrainType(terrain) {
    this.currentConditions.terrain = terrain;

    switch (terrain) {
      case 'underwater':
        this.applyEffect(null, 'underwater', 1.0);
        break;
      case 'cave':
        // Apply echo effect for caves
        this.applyEffect(null, 'echo', 0.6);
        break;
      case 'forest':
        // Apply light wind and bird sounds (would need bird generator)
        this.applyEffect(null, 'wind', 0.2);
        break;
      case 'indoor':
        // Remove outdoor effects
        this.applyEffect(null, 'rain', 0);
        this.applyEffect(null, 'wind', 0);
        break;
    }

    this.emit('terrainChanged', { terrain });
  }

  /**
   * Update environmental conditions
   */
  updateConditions(conditions) {
    Object.assign(this.currentConditions, conditions);

    if (conditions.weather !== undefined) {
      this.setWeatherConditions(conditions.weather, conditions.intensity || 0.5);
    }

    if (conditions.terrain !== undefined) {
      this.setTerrainType(conditions.terrain);
    }

    this.emit('conditionsUpdated', this.currentConditions);
  }

  /**
   * Get current environmental conditions
   */
  getCurrentConditions() {
    return { ...this.currentConditions };
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
          console.error(`Error in environmental effects event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup and destroy environmental effects
   */
  cleanup() {
    // Stop all ambient generators
    for (const [type, generator] of this.ambientGenerators) {
      if (generator.source) {
        generator.source.stop();
      }
      if (generator.lfo) {
        generator.lfo.stop();
      }
      if (generator.stop) {
        generator.stop();
      }
      if (generator.gain) {
        generator.gain.disconnect();
      }
    }

    // Clear all references
    this.ambientGenerators.clear();
    this.effectProcessors.clear();

    if (this.eventListeners) {
      this.eventListeners.clear();
    }
  }
}