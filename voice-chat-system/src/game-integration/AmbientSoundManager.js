/**
 * Ambient Sound Manager - Manages environmental and ambient audio
 * Provides dynamic ambient sounds that react to game state and environment
 */

export class AmbientSoundManager {
  constructor(audioContext, config = {}) {
    this.audioContext = audioContext;
    this.config = {
      volume: 0.3,
      dynamicAmbient: true,
      weatherEffects: true,
      dayNightCycle: true,
      locationBasedAmbient: true,
      crossfadeTime: 2.0, // seconds
      ...config
    };

    // Ambient sound library
    this.ambientLibrary = {
      locations: new Map(),
      weather: new Map(),
      timeOfDay: new Map(),
      combat: new Map()
    };

    // Current ambient state
    this.currentState = {
      location: 'default',
      weather: 'clear',
      timeOfDay: 'day',
      inCombat: false,
      intensity: 0.5
    };

    // Active ambient sounds
    this.activeAmbients = new Map();
    this.crossfadingAmbients = new Map();

    // Ambient sound generators
    this.generators = {
      wind: null,
      rain: null,
      birds: null,
      insects: null,
      water: null,
      fire: null,
      machinery: null,
      magical: null
    };

    // Event system
    this.eventListeners = new Map();

    // Performance monitoring
    this.metrics = {
      activeSounds: 0,
      memoryUsage: 0,
      cpuUsage: 0
    };

    // Initialize ambient sounds
    this.initializeAmbientLibrary();
  }

  /**
   * Initialize ambient sound library
   */
  initializeAmbientLibrary() {
    // Location-based ambient sounds
    this.ambientLibrary.locations.set('forest', {
      name: 'Forest',
      components: ['birds', 'insects', 'wind', 'leaves'],
      baseIntensity: 0.6,
      characteristics: { reverb: 0.2, warmth: 1.2 }
    });

    this.ambientLibrary.locations.set('dungeon', {
      name: 'Dungeon',
      components: ['drip', 'echo', 'distantMachinery', 'creaks'],
      baseIntensity: 0.4,
      characteristics: { reverb: 0.8, muffled: true }
    });

    this.ambientLibrary.locations.set('cave', {
      name: 'Cave',
      components: ['drip', 'wind', 'echo', 'bats'],
      baseIntensity: 0.3,
      characteristics: { reverb: 0.9, lowFreq: true }
    });

    this.ambientLibrary.locations.set('town', {
      name: 'Town',
      components: ['crowd', 'blacksmith', 'market', 'children'],
      baseIntensity: 0.7,
      characteristics: { brightness: 1.1 }
    });

    this.ambientLibrary.locations.set('battlefield', {
      name: 'Battlefield',
      components: ['wind', 'distantFighting', 'crows', 'fire'],
      baseIntensity: 0.8,
      characteristics: { harshness: 1.3 }
    });

    this.ambientLibrary.locations.set('magicalTower', {
      name: 'Magical Tower',
      components: ['crystals', 'enchantedWind', 'spells', 'energy'],
      baseIntensity: 0.5,
      characteristics: { magical: true, ethereal: 0.8 }
    });

    // Weather-based ambient sounds
    this.ambientLibrary.weather.set('clear', {
      name: 'Clear',
      components: ['birds', 'gentleWind'],
      intensity: 0.3
    });

    this.ambientLibrary.weather.set('rain', {
      name: 'Rain',
      components: ['rain', 'thunder', 'wind'],
      intensity: 0.7
    });

    this.ambientLibrary.weather.set('storm', {
      name: 'Storm',
      components: ['heavyRain', 'thunder', 'strongWind', 'lightning'],
      intensity: 1.0
    });

    this.ambientLibrary.weather.set('snow', {
      name: 'Snow',
      components: ['wind', 'snowfall', 'quiet'],
      intensity: 0.4
    });

    this.ambientLibrary.weather.set('fog', {
      name: 'Fog',
      components: ['quiet', 'mutedWind', 'distantSounds'],
      intensity: 0.2
    });

    // Time of day ambient sounds
    this.ambientLibrary.timeOfDay.set('dawn', {
      name: 'Dawn',
      components: ['birds', 'morningWind', 'cricketsFading'],
      intensity: 0.4
    });

    this.ambientLibrary.timeOfDay.set('day', {
      name: 'Day',
      components: ['birds', 'activity', 'sunnyAmbience'],
      intensity: 0.6
    });

    this.ambientLibrary.timeOfDay.set('dusk', {
      name: 'Dusk',
      components: ['crickets', 'eveningWind', 'owls'],
      intensity: 0.5
    });

    this.ambientLibrary.timeOfDay.set('night', {
      name: 'Night',
      components: ['crickets', 'owls', 'nightWind', 'wolves'],
      intensity: 0.3
    });

    // Combat ambient sounds
    this.ambientLibrary.combat.set('preparation', {
      name: 'Combat Preparation',
      components: ['tension', 'heavyBreathing', 'weaponClangs'],
      intensity: 0.6
    });

    this.ambientLibrary.combat.set('active', {
      name: 'Active Combat',
      components: ['intenseMusic', 'shouts', 'weaponHits', 'spells'],
      intensity: 1.0
    });

    this.ambientLibrary.combat.set('aftermath', {
      name: 'Combat Aftermath',
      components: ['wounded', 'fireEmbers', 'quietTension'],
      intensity: 0.4
    });
  }

  /**
   * Initialize ambient sound manager
   */
  async initialize() {
    try {
      // Initialize ambient sound generators
      await this.initializeAmbientGenerators();

      // Set initial ambient state
      this.setAmbientState(this.currentState);

      // Start performance monitoring
      this.startPerformanceMonitoring();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize ambient sound manager:', error);
      throw error;
    }
  }

  /**
   * Initialize ambient sound generators
   */
  async initializeAmbientGenerators() {
    // Wind generator
    this.generators.wind = await this.createWindGenerator();

    // Rain generator
    this.generators.rain = await this.createRainGenerator();

    // Birds generator
    this.generators.birds = await this.createBirdsGenerator();

    // Insects generator
    this.generators.insects = await this.createInsectsGenerator();

    // Water generator
    this.generators.water = await this.createWaterGenerator();

    // Fire generator
    this.generators.fire = await this.createFireGenerator();

    // Magical generator
    this.generators.magical = await this.createMagicalGenerator();
  }

  /**
   * Create wind ambient generator
   */
  async createWindGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 100,
        intensity: 0.5,
        variation: 0.3
      }
    };

    const windNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    windNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Base wind sound
        const wind = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate);
        sample += wind * generator.parameters.intensity;

        // Wind gusts
        if (Math.random() < 0.01) {
          sample += (Math.random() - 0.5) * generator.parameters.variation;
        }

        // High frequency whistle
        sample += Math.sin(2 * Math.PI * 2000 * i / this.audioContext.sampleRate) * 0.05;

        outputBuffer[i] = sample;
      }
    };

    generator.node = windNode;
    return generator;
  }

  /**
   * Create rain ambient generator
   */
  async createRainGenerator() {
    const generator = {
      node: null,
      parameters: {
        intensity: 0.5,
        dropFrequency: 100,
        splashIntensity: 0.3
      }
    };

    const rainNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    rainNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Rain drops
        if (Math.random() < generator.parameters.intensity * 0.1) {
          sample += (Math.random() - 0.5) * 0.3;
        }

        // Continuous rain noise
        sample += (Math.random() - 0.5) * 0.05;

        outputBuffer[i] = sample;
      }
    };

    generator.node = rainNode;
    return generator;
  }

  /**
   * Create birds ambient generator
   */
  async createBirdsGenerator() {
    const generator = {
      node: null,
      parameters: {
        activity: 0.6,
        variety: 5,
        callFrequency: 0.1
      }
    };

    const birdsNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    birdsNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Bird calls
        if (Math.random() < generator.parameters.callFrequency * generator.parameters.activity) {
          const birdType = Math.floor(Math.random() * generator.parameters.variety);
          const frequency = 1000 + birdType * 500;
          sample += Math.sin(2 * Math.PI * frequency * i / this.audioContext.sampleRate) * 0.2;
        }

        outputBuffer[i] = sample;
      }
    };

    generator.node = birdsNode;
    return generator;
  }

  /**
   * Create insects ambient generator
   */
  async createInsectsGenerator() {
    const generator = {
      node: null,
      parameters: {
        chirpRate: 0.2,
        frequency: 3000,
        intensity: 0.3
      }
    };

    const insectsNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    insectsNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Cricket chirps
        if (Math.random() < generator.parameters.chirpRate) {
          sample += Math.sin(2 * Math.PI * generator.parameters.frequency * i / this.audioContext.sampleRate) * generator.parameters.intensity;
        }

        outputBuffer[i] = sample;
      }
    };

    generator.node = insectsNode;
    return generator;
  }

  /**
   * Create water ambient generator
   */
  async createWaterGenerator() {
    const generator = {
      node: null,
      parameters: {
        flowRate: 0.5,
        rippleFrequency: 500,
        splashIntensity: 0.2
      }
    };

    const waterNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    waterNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Water flow
        const flow = Math.sin(2 * Math.PI * generator.parameters.rippleFrequency * i / this.audioContext.sampleRate);
        sample += flow * generator.parameters.flowRate;

        // Occasional splashes
        if (Math.random() < 0.01) {
          sample += (Math.random() - 0.5) * generator.parameters.splashIntensity;
        }

        outputBuffer[i] = sample;
      }
    };

    generator.node = waterNode;
    return generator;
  }

  /**
   * Create fire ambient generator
   */
  async createFireGenerator() {
    const generator = {
      node: null,
      parameters: {
        crackleIntensity: 0.4,
        roarLevel: 0.3,
        emberSounds: true
      }
    };

    const fireNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    fireNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Fire crackle
        if (Math.random() < generator.parameters.crackleIntensity) {
          sample += (Math.random() - 0.5) * 0.3;
        }

        // Low frequency roar
        sample += Math.sin(2 * Math.PI * 80 * i / this.audioContext.sampleRate) * generator.parameters.roarLevel;

        outputBuffer[i] = sample;
      }
    };

    generator.node = fireNode;
    return generator;
  }

  /**
   * Create magical ambient generator
   */
  async createMagicalGenerator() {
    const generator = {
      node: null,
      parameters: {
        energyLevel: 0.5,
        harmonicContent: 0.7,
        mysticalQuality: 0.8
      }
    };

    const magicalNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    magicalNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Magical harmonics
        sample += Math.sin(2 * Math.PI * 440 * i / this.audioContext.sampleRate) * generator.parameters.energyLevel;
        sample += Math.sin(2 * Math.PI * 880 * i / this.audioContext.sampleRate) * generator.parameters.harmonicContent * 0.5;
        sample += Math.sin(2 * Math.PI * 1320 * i / this.audioContext.sampleRate) * generator.parameters.harmonicContent * 0.3;

        // Ethereal quality
        sample *= Math.sin(2 * Math.PI * 0.5 * i / this.audioContext.sampleRate) * 0.5 + 0.5;

        outputBuffer[i] = sample * generator.parameters.mysticalQuality;
      }
    };

    generator.node = magicalNode;
    return generator;
  }

  /**
   * Set ambient state
   */
  setAmbientState(newState) {
    const previousState = { ...this.currentState };
    Object.assign(this.currentState, newState);

    // Update ambient sounds based on new state
    this.updateAmbientSounds(previousState, this.currentState);

    this.emit('ambientStateChanged', {
      previousState,
      currentState: this.currentState
    });
  }

  /**
   * Update ambient sounds based on state changes
   */
  updateAmbientSounds(previousState, currentState) {
    // Check for location change
    if (previousState.location !== currentState.location) {
      this.crossfadeLocationAmbient(previousState.location, currentState.location);
    }

    // Check for weather change
    if (previousState.weather !== currentState.weather) {
      this.updateWeatherAmbient(currentState.weather);
    }

    // Check for time of day change
    if (previousState.timeOfDay !== currentState.timeOfDay) {
      this.updateTimeOfDayAmbient(currentState.timeOfDay);
    }

    // Check for combat state change
    if (previousState.inCombat !== currentState.inCombat) {
      this.updateCombatAmbient(currentState.inCombat);
    }
  }

  /**
   * Crossfade between location ambient sounds
   */
  crossfadeLocationAmbient(oldLocation, newLocation) {
    const oldAmbient = this.ambientLibrary.locations.get(oldLocation);
    const newAmbient = this.ambientLibrary.locations.get(newLocation);

    if (!newAmbient) return;

    // Stop old location ambience
    if (oldAmbient) {
      this.stopLocationAmbient(oldLocation);
    }

    // Start new location ambience
    this.startLocationAmbient(newLocation);

    this.emit('locationChanged', { oldLocation, newLocation });
  }

  /**
   * Start location ambient sound
   */
  startLocationAmbient(location) {
    const ambientData = this.ambientLibrary.locations.get(location);
    if (!ambientData) return;

    const ambientId = `location_${location}`;

    // Create gain node for this ambient
    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = 0;

    // Start appropriate generators
    ambientData.components.forEach(component => {
      this.startAmbientComponent(component, gainNode);
    });

    // Store active ambient
    this.activeAmbients.set(ambientId, {
      type: 'location',
      name: location,
      gainNode,
      components: ambientData.components,
      intensity: ambientData.baseIntensity
    });

    // Fade in
    gainNode.gain.linearRampToValueAtTime(
      ambientData.baseIntensity * this.config.volume,
      this.audioContext.currentTime + this.config.crossfadeTime
    );
  }

  /**
   * Stop location ambient sound
   */
  stopLocationAmbient(location) {
    const ambientId = `location_${location}`;
    const ambient = this.activeAmbients.get(ambientId);

    if (!ambient) return;

    // Fade out
    ambient.gainNode.gain.linearRampToValueAtTime(
      0,
      this.audioContext.currentTime + this.config.crossfadeTime
    );

    // Stop after fade out
    setTimeout(() => {
      ambient.components.forEach(component => {
        this.stopAmbientComponent(component);
      });
      ambient.gainNode.disconnect();
      this.activeAmbients.delete(ambientId);
    }, this.config.crossfadeTime * 1000);
  }

  /**
   * Start ambient component
   */
  startAmbientComponent(component, gainNode) {
    const generator = this.generators[component];
    if (!generator) return;

    // Create component-specific processing if needed
    const componentGain = this.audioContext.createGain();
    componentGain.gain.value = 1.0;

    // Connect generator to gain
    if (generator.node) {
      generator.node.connect(componentGain);
      componentGain.connect(gainNode);
    }

    // Mark component as active
    generator.active = true;
  }

  /**
   * Stop ambient component
   */
  stopAmbientComponent(component) {
    const generator = this.generators[component];
    if (!generator) return;

    if (generator.node) {
      generator.node.disconnect();
    }

    generator.active = false;
  }

  /**
   * Update weather ambient
   */
  updateWeatherAmbient(weather) {
    const weatherData = this.ambientLibrary.weather.get(weather);
    if (!weatherData) return;

    // Apply weather effects to existing ambients
    weatherData.components.forEach(component => {
      this.applyWeatherEffect(component, weatherData.intensity);
    });

    this.emit('weatherChanged', { weather });
  }

  /**
   * Update time of day ambient
   */
  updateTimeOfDayAmbient(timeOfDay) {
    const timeData = this.ambientLibrary.timeOfDay.get(timeOfDay);
    if (!timeData) return;

    // Adjust existing ambients for time of day
    Object.values(this.activeAmbients).forEach(ambient => {
      if (ambient.gainNode) {
        const newGain = ambient.intensity * timeData.intensity * this.config.volume;
        ambient.gainNode.gain.linearRampToValueAtTime(
          newGain,
          this.audioContext.currentTime + 1.0
        );
      }
    });

    this.emit('timeOfDayChanged', { timeOfDay });
  }

  /**
   * Update combat ambient
   */
  updateCombatAmbient(inCombat) {
    if (inCombat) {
      // Start combat ambience
      this.startCombatAmbient();
    } else {
      // Stop combat ambience
      this.stopCombatAmbient();
    }

    this.emit('combatStateChanged', { inCombat });
  }

  /**
   * Start combat ambient
   */
  startCombatAmbient() {
    const combatData = this.ambientLibrary.combat.get('active');
    if (!combatData) return;

    const ambientId = 'combat_active';

    // Create combat-specific processing
    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = 0;

    // Add tension filter
    const tensionFilter = this.audioContext.createBiquadFilter();
    tensionFilter.type = 'lowshelf';
    tensionFilter.frequency.value = 200;
    tensionFilter.gain.value = 3; // Boost low frequencies for tension

    // Start combat components
    combatData.components.forEach(component => {
      // Create combat-specific sounds
      this.createCombatSound(component, gainNode);
    });

    // Connect processing chain
    gainNode.connect(tensionFilter);
    tensionFilter.connect(this.audioContext.destination);

    // Store active ambient
    this.activeAmbients.set(ambientId, {
      type: 'combat',
      name: 'active',
      gainNode,
      tensionFilter,
      intensity: combatData.intensity
    });

    // Fade in
    gainNode.gain.linearRampToValueAtTime(
      combatData.intensity * this.config.volume,
      this.audioContext.currentTime + 0.5
    );
  }

  /**
   * Stop combat ambient
   */
  stopCombatAmbient() {
    const ambientId = 'combat_active';
    const ambient = this.activeAmbients.get(ambientId);

    if (!ambient) return;

    // Fade out
    ambient.gainNode.gain.linearRampToValueAtTime(
      0,
      this.audioContext.currentTime + 1.0
    );

    // Stop after fade out
    setTimeout(() => {
      ambient.gainNode.disconnect();
      ambient.tensionFilter.disconnect();
      this.activeAmbients.delete(ambientId);
    }, 1000);
  }

  /**
   * Create combat-specific sound
   */
  createCombatSound(component, gainNode) {
    // Create combat sound generators
    switch (component) {
      case 'intenseMusic':
        // Would create intense musical theme
        break;
      case 'shouts':
        // Would create battle shout sounds
        break;
      case 'weaponHits':
        // Would integrate with combat sound effects
        break;
      case 'spells':
        // Would integrate with spell audio processor
        break;
    }
  }

  /**
   * Apply weather effect to ambient
   */
  applyWeatherEffect(component, intensity) {
    const generator = this.generators[component];
    if (!generator || !generator.node) return;

    // Adjust generator parameters based on weather
    switch (component) {
      case 'wind':
        if (generator.parameters) {
          generator.parameters.intensity = intensity;
        }
        break;
      case 'rain':
        if (generator.parameters) {
          generator.parameters.intensity = intensity;
        }
        break;
    }
  }

  /**
   * Set combat mode
   */
  setCombatMode(inCombat) {
    this.setAmbientState({ inCombat });
  }

  /**
   * Set location
   */
  setLocation(location) {
    this.setAmbientState({ location });
  }

  /**
   * Set weather
   */
  setWeather(weather) {
    this.setAmbientState({ weather });
  }

  /**
   * Set time of day
   */
  setTimeOfDay(timeOfDay) {
    this.setAmbientState({ timeOfDay });
  }

  /**
   * Set volume
   */
  setVolume(volume) {
    this.config.volume = Math.max(0, Math.min(1, volume));

    // Update all active ambients
    Object.values(this.activeAmbients).forEach(ambient => {
      if (ambient.gainNode && ambient.intensity) {
        ambient.gainNode.gain.value = ambient.intensity * this.config.volume;
      }
    });

    this.emit('volumeChanged', { volume: this.config.volume });
  }

  /**
   * Start performance monitoring
   */
  startPerformanceMonitoring() {
    setInterval(() => {
      this.metrics.activeSounds = this.activeAmbients.size;
      this.metrics.memoryUsage = this.estimateMemoryUsage();
    }, 1000);
  }

  /**
   * Estimate memory usage
   */
  estimateMemoryUsage() {
    let usage = 0;

    // Estimate based on active sounds and generators
    usage += this.activeAmbients.size * 1024; // 1KB per ambient
    usage += Object.keys(this.generators).length * 512; // 512B per generator

    return usage;
  }

  /**
   * Get metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      currentState: { ...this.currentState },
      activeAmbients: Array.from(this.activeAmbients.keys()),
      librarySizes: {
        locations: this.ambientLibrary.locations.size,
        weather: this.ambientLibrary.weather.size,
        timeOfDay: this.ambientLibrary.timeOfDay.size,
        combat: this.ambientLibrary.combat.size
      }
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
          console.error(`Error in ambient sound manager event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup ambient sound manager
   */
  cleanup() {
    // Stop all active ambients
    for (const [ambientId, ambient] of this.activeAmbients) {
      ambient.gainNode.disconnect();
      if (ambient.tensionFilter) {
        ambient.tensionFilter.disconnect();
      }
    }

    this.activeAmbients.clear();

    // Stop all generators
    Object.values(this.generators).forEach(generator => {
      if (generator && generator.node) {
        generator.node.disconnect();
      }
    });

    this.eventListeners.clear();
  }
}