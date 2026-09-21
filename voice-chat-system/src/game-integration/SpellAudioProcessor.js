/**
 * Spell Audio Processor - Handles spell casting audio effects
 * Provides magical sound effects, incantation processing, and spell audio feedback
 */

export class SpellAudioProcessor {
  constructor(audioContext, config = {}) {
    this.audioContext = audioContext;
    this.config = {
      volume: 0.8,
      preparationTime: 2000, // ms
      echoEnabled: true,
      spellVariations: true,
      magicalAmbience: true,
      ...config
    };

    // Spell definitions with audio characteristics
    this.spellDefinitions = new Map([
      ['fireball', {
        school: 'evocation',
        element: 'fire',
        castingTime: 2000,
        soundProfile: {
          frequency: 150,
          harmonics: [1, 1.5, 2, 2.5],
          envelope: { attack: 0.1, decay: 0.3, sustain: 0.6, release: 0.8 },
          effects: ['fire', 'explosion']
        }
      }],
      ['lightningBolt', {
        school: 'evocation',
        element: 'lightning',
        castingTime: 1500,
        soundProfile: {
          frequency: 300,
          harmonics: [1, 2, 3, 4],
          envelope: { attack: 0.01, decay: 0.1, sustain: 0.2, release: 0.3 },
          effects: ['electricity', 'crackle']
        }
      }],
      ['heal', {
        school: 'conjuration',
        element: 'life',
        castingTime: 3000,
        soundProfile: {
          frequency: 400,
          harmonics: [1, 2, 3, 5],
          envelope: { attack: 0.3, decay: 0.2, sustain: 0.8, release: 0.9 },
          effects: ['chorus', 'reverb', 'healing']
        }
      }],
      ['invisibility', {
        school: 'illusion',
        element: 'void',
        castingTime: 2500,
        soundProfile: {
          frequency: 800,
          harmonics: [1, 1.618, 2.618],
          envelope: { attack: 0.5, decay: 0.8, sustain: 0.3, release: 1.2 },
          effects: ['phase', 'shimmer']
        }
      }],
      ['teleport', {
        school: 'conjuration',
        element: 'space',
        castingTime: 4000,
        soundProfile: {
          frequency: 200,
          harmonics: [1, 1.414, 2, 2.828],
          envelope: { attack: 0.8, decay: 0.6, sustain: 0.4, release: 1.5 },
          effects: ['whoosh', 'spatial', 'reverb']
        }
      }],
      ['shield', {
        school: 'abjuration',
        element: 'force',
        castingTime: 1000,
        soundProfile: {
          frequency: 600,
          harmonics: [1, 1.732, 3],
          envelope: { attack: 0.1, decay: 0.2, sustain: 1.0, release: 0.4 },
          effects: ['barrier', 'resonance']
        }
      }]
    ]);

    // Active spell sounds
    this.activeSpells = new Map();

    // Spell preparation state
    this.preparationState = new Map();

    // Magical sound generators
    this.soundGenerators = {
      fire: null,
      electricity: null,
      water: null,
      earth: null,
      air: null,
      life: null,
      void: null,
      space: null
    };

    // Event system
    this.eventListeners = new Map();

    // Performance metrics
    this.metrics = {
      spellsCast: 0,
      spellsPreparing: 0,
      averageCastingTime: 0,
      activeSpellCount: 0
    };
  }

  /**
   * Initialize spell audio processor
   */
  async initialize() {
    try {
      // Initialize magical sound generators
      await this.initializeMagicalGenerators();

      // Load audio worklets for spell processing
      await this.loadSpellWorklets();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize spell audio processor:', error);
      throw error;
    }
  }

  /**
   * Initialize magical sound generators
   */
  async initializeMagicalGenerators() {
    // Fire generator
    this.soundGenerators.fire = await this.createFireGenerator();

    // Electricity generator
    this.soundGenerators.electricity = await this.createElectricityGenerator();

    // Water generator
    this.soundGenerators.water = await this.createWaterGenerator();

    // Earth generator
    this.soundGenerators.earth = await this.createEarthGenerator();

    // Air generator
    this.soundGenerators.air = await this.createAirGenerator();

    // Life generator
    this.soundGenerators.life = await this.createLifeGenerator();

    // Void generator
    this.soundGenerators.void = await this.createVoidGenerator();

    // Space generator
    this.soundGenerators.space = await this.createSpaceGenerator();
  }

  /**
   * Create fire sound generator
   */
  async createFireGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 150,
        harmonics: [1, 1.5, 2, 2.5],
        crackleIntensity: 0.8,
        roarLevel: 0.6
      }
    };

    const fireNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    fireNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        // Generate fire sound with multiple components
        let sample = 0;

        // Low frequency roar
        const roar = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate) * 0.3;
        sample += roar;

        // Harmonics for fuller sound
        generator.parameters.harmonics.forEach((harmonic, index) => {
          const harmonicFreq = generator.parameters.baseFrequency * harmonic;
          const harmonicSample = Math.sin(2 * Math.PI * harmonicFreq * i / this.audioContext.sampleRate) * 0.1 / (index + 1);
          sample += harmonicSample;
        });

        // Crackling sounds
        if (Math.random() < generator.parameters.crackleIntensity * 0.1) {
          sample += (Math.random() - 0.5) * 0.5;
        }

        outputBuffer[i] = sample * generator.parameters.roarLevel;
      }
    };

    generator.node = fireNode;
    return generator;
  }

  /**
   * Create electricity sound generator
   */
  async createElectricityGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 300,
        noiseLevel: 0.7,
        crackleRate: 0.3
      }
    };

    const electricityNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    electricityNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // High frequency electrical hum
        const hum = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate) * 0.4;
        sample += hum;

        // Electrical noise and crackle
        if (Math.random() < generator.parameters.crackleRate) {
          sample += (Math.random() - 0.5) * generator.parameters.noiseLevel;
        }

        // Rapid fluctuations
        sample += Math.sin(2 * Math.PI * generator.parameters.baseFrequency * 10 * i / this.audioContext.sampleRate) * 0.1;

        outputBuffer[i] = sample;
      }
    };

    generator.node = electricityNode;
    return generator;
  }

  /**
   * Create water sound generator
   */
  async createWaterGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 200,
        flowRate: 0.5,
        bubbleIntensity: 0.3
      }
    };

    const waterNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    waterNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Water flow sound
        const flow = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate) * generator.parameters.flowRate;
        sample += flow;

        // Bubbling sounds
        if (Math.random() < generator.parameters.bubbleIntensity * 0.05) {
          const bubbleFreq = 800 + Math.random() * 400;
          const bubble = Math.sin(2 * Math.PI * bubbleFreq * i / this.audioContext.sampleRate) * 0.2;
          sample += bubble * Math.exp(-Math.random() * 10);
        }

        outputBuffer[i] = sample;
      }
    };

    generator.node = waterNode;
    return generator;
  }

  /**
   * Create earth sound generator
   */
  async createEarthGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 80,
        rumbleIntensity: 0.8,
        gravelNoise: 0.4
      }
    };

    const earthNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    earthNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Low frequency rumble
        const rumble = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate) * generator.parameters.rumbleIntensity;
        sample += rumble;

        // Gravel and rock sounds
        if (Math.random() < generator.parameters.gravelNoise * 0.1) {
          sample += (Math.random() - 0.5) * 0.3;
        }

        outputBuffer[i] = sample;
      }
    };

    generator.node = earthNode;
    return generator;
  }

  /**
   * Create air sound generator
   */
  async createAirGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 250,
        windIntensity: 0.6,
        whistleLevel: 0.3
      }
    };

    const airNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    airNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Wind sound
        const wind = (Math.random() - 0.5) * generator.parameters.windIntensity;
        sample += wind;

        // Whistling sounds
        const whistle = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate) * generator.parameters.whistleLevel;
        sample += whistle;

        outputBuffer[i] = sample;
      }
    };

    generator.node = airNode;
    return generator;
  }

  /**
   * Create life sound generator
   */
  async createLifeGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 400,
        harmonyLevel: 0.8,
        pulseRate: 2 // Hz
      }
    };

    const lifeNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    lifeNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Life pulse/beating sound
        const pulse = Math.sin(2 * Math.PI * generator.parameters.pulseRate * i / this.audioContext.sampleRate) * 0.3;
        sample += pulse;

        // Harmonious frequencies
        const harmony = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate) * generator.parameters.harmonyLevel;
        sample += harmony;

        // Additional harmonics for life sound
        sample += Math.sin(2 * Math.PI * generator.parameters.baseFrequency * 1.618 * i / this.audioContext.sampleRate) * 0.2;
        sample += Math.sin(2 * Math.PI * generator.parameters.baseFrequency * 2.618 * i / this.audioContext.sampleRate) * 0.1;

        outputBuffer[i] = sample;
      }
    };

    generator.node = lifeNode;
    return generator;
  }

  /**
   * Create void sound generator
   */
  async createVoidGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 800,
        emptinessLevel: 0.9,
        phaseShift: 0.5
      }
    };

    const voidNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    voidNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Void sound - high frequency with phase shifting
        const voidSound = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate + generator.parameters.phaseShift);
        sample += voidSound * generator.parameters.emptinessLevel;

        // Phase modulation for otherworldly effect
        generator.parameters.phaseShift += 0.01;

        outputBuffer[i] = sample * 0.5;
      }
    };

    generator.node = voidNode;
    return generator;
  }

  /**
   * Create space sound generator
   */
  async createSpaceGenerator() {
    const generator = {
      node: null,
      parameters: {
        baseFrequency: 200,
        spatialEffect: 0.8,
        dimensionalShift: 0.3
      }
    };

    const spaceNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    spaceNode.onaudioprocess = (e) => {
      const outputBuffer = e.outputBuffer.getChannelData(0);

      for (let i = 0; i < outputBuffer.length; i++) {
        let sample = 0;

        // Space/time bending sound
        const spaceSound = Math.sin(2 * Math.PI * generator.parameters.baseFrequency * i / this.audioContext.sampleRate);
        sample += spaceSound * generator.parameters.spatialEffect;

        // Dimensional shifting effect
        sample += Math.sin(2 * Math.PI * generator.parameters.baseFrequency * Math.sqrt(2) * i / this.audioContext.sampleRate) * generator.parameters.dimensionalShift;

        outputBuffer[i] = sample * 0.6;
      }
    };

    generator.node = spaceNode;
    return generator;
  }

  /**
   * Load spell processing audio worklets
   */
  async loadSpellWorklets() {
    const worklets = [
      'spell-processor.js',
      'magical-effects.js',
      'spatial-magic.js'
    ];

    for (const worklet of worklets) {
      try {
        await this.audioContext.audioWorklet.addModule(`/worklets/${worklets}`);
      } catch (error) {
        console.warn(`Failed to load spell worklet ${worklet}:`, error);
      }
    }
  }

  /**
   * Cast a spell with audio effects
   */
  async castSpell(spellName, caster, target) {
    try {
      const spell = this.spellDefinitions.get(spellName);
      if (!spell) {
        console.warn(`Unknown spell: ${spellName}`);
        return;
      }

      // Start spell preparation
      await this.prepareSpell(spell, caster);

      // Create spell sound
      const spellSound = await this.createSpellSound(spell);

      // Play spell sound with spatial positioning
      this.playSpellSound(spellSound, spell, caster, target);

      // Update metrics
      this.metrics.spellsCast++;
      this.metrics.activeSpellCount++;

      // Create spell ID for tracking
      const spellId = `${spellName}_${Date.now()}_${Math.random()}`;

      // Track active spell
      this.activeSpells.set(spellId, {
        spell,
        caster,
        target,
        startTime: this.audioContext.currentTime,
        duration: spell.castingTime / 1000
      });

      // Clean up after spell duration
      setTimeout(() => {
        this.activeSpells.delete(spellId);
        this.metrics.activeSpellCount--;
      }, spell.castingTime);

      this.emit('spellCast', {
        spellName,
        spell,
        caster,
        target,
        duration: spell.castingTime,
        spellId
      });

    } catch (error) {
      console.error('Failed to cast spell:', error);
      this.emit('spellError', { spellName, error });
    }
  }

  /**
   * Prepare spell with incantation sounds
   */
  async prepareSpell(spell, caster) {
    const preparationId = `${spell.school}_${caster.id}_${Date.now()}`;

    this.preparationState.set(preparationId, {
      spell,
      caster,
      startTime: Date.now(),
      isComplete: false
    });

    this.metrics.spellsPreparing++;

    // Create preparation sound
    const preparationSound = this.createPreparationSound(spell);

    // Play preparation sound at caster location
    this.playPreparationSound(preparationSound, spell, caster);

    // Wait for preparation time
    await new Promise(resolve => {
      setTimeout(() => {
        this.preparationState.get(preparationId).isComplete = true;
        this.preparationState.delete(preparationId);
        this.metrics.spellsPreparing--;
        resolve();
      }, spell.castingTime);
    });

    this.emit('spellPrepared', {
      spell: spell.school,
      caster,
      preparationTime: spell.castingTime
    });
  }

  /**
   * Create spell sound buffer
   */
  async createSpellSound(spell) {
    const duration = spell.castingTime / 1000;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);

    const soundProfile = spell.soundProfile;

    for (let channel = 0; channel < 2; channel++) {
      const channelData = buffer.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        const time = i / sampleRate;
        let sample = 0;

        // Apply envelope
        const envelope = this.calculateEnvelope(time, soundProfile.envelope, duration);

        // Generate base frequency with harmonics
        soundProfile.harmonics.forEach((harmonic, index) => {
          const frequency = soundProfile.frequency * harmonic;
          const harmonicSample = Math.sin(2 * Math.PI * frequency * time) * (1 / (index + 1));
          sample += harmonicSample;
        });

        // Apply magical effects
        sample = this.applyMagicalEffects(sample, soundProfile.effects, time);

        // Apply envelope
        sample *= envelope;

        channelData[i] = sample * this.config.volume;
      }
    }

    return buffer;
  }

  /**
   * Calculate ADSR envelope
   */
  calculateEnvelope(time, envelope, duration) {
    const { attack, decay, sustain, release } = envelope;
    const totalTime = attack + decay + sustain + release;

    if (time < attack) {
      return time / attack;
    } else if (time < attack + decay) {
      const progress = (time - attack) / decay;
      return 1 - (1 - sustain) * progress;
    } else if (time < attack + decay + sustain) {
      return sustain;
    } else if (time < totalTime) {
      const progress = (time - attack - decay - sustain) / release;
      return sustain * (1 - progress);
    } else {
      return 0;
    }
  }

  /**
   * Apply magical effects to sound
   */
  applyMagicalEffects(sample, effects, time) {
    effects.forEach(effect => {
      switch (effect) {
        case 'fire':
          sample += Math.sin(2 * Math.PI * 150 * time) * 0.2;
          sample += (Math.random() - 0.5) * 0.1;
          break;
        case 'electricity':
          if (Math.random() < 0.1) {
            sample += (Math.random() - 0.5) * 0.5;
          }
          break;
        case 'healing':
          sample *= 1 + Math.sin(2 * Math.PI * 5 * time) * 0.1;
          break;
        case 'reverb':
          // Simple reverb effect (would use convolution reverb in production)
          sample += sample * 0.3 * Math.exp(-time * 2);
          break;
        case 'chorus':
          sample += Math.sin(2 * Math.PI * (400 + Math.sin(2 * Math.PI * 2 * time) * 50) * time) * 0.2;
          break;
        case 'phase':
          sample = Math.sin(2 * Math.PI * 800 * time + Math.sin(2 * Math.PI * 3 * time) * 0.5) * 0.5;
          break;
        case 'spatial':
          sample *= Math.sin(2 * Math.PI * 0.5 * time) * 0.5 + 0.5;
          break;
        case 'barrier':
          sample += Math.sin(2 * Math.PI * 600 * time) * 0.3;
          break;
        case 'explosion':
          sample *= 1 + Math.exp(-time * 10) * 2;
          break;
        case 'crackle':
          if (Math.random() < 0.2) {
            sample += (Math.random() - 0.5) * 0.8;
          }
          break;
        case 'whoosh':
          sample += Math.sin(2 * Math.PI * 200 * time) * Math.exp(-time * 3) * 0.4;
          break;
        case 'shimmer':
          sample += Math.sin(2 * Math.PI * 1200 * time) * 0.1 * Math.sin(2 * Math.PI * 8 * time);
          break;
      }
    });

    return sample;
  }

  /**
   * Create preparation sound
   */
  createPreparationSound(spell) {
    const duration = spell.castingTime / 1000;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);

    for (let channel = 0; channel < 2; channel++) {
      const channelData = buffer.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        const time = i / sampleRate;

        // Low frequency humming during preparation
        let sample = Math.sin(2 * Math.PI * spell.soundProfile.frequency * 0.5 * time) * 0.3;

        // Gradual intensity increase
        const intensity = time / duration;
        sample *= intensity;

        // Add magical shimmer
        sample += Math.sin(2 * Math.PI * 1000 * time) * 0.1 * intensity;

        channelData[i] = sample * this.config.volume * 0.5;
      }
    }

    return buffer;
  }

  /**
   * Play spell sound with spatial positioning
   */
  playSpellSound(soundBuffer, spell, caster, target) {
    const source = this.audioContext.createBufferSource();
    source.buffer = soundBuffer;

    // Create spatial positioning
    const panner = this.audioContext.createPanner();
    panner.panningModel = 'HRTF';
    panner.distanceModel = 'inverse';
    panner.refDistance = 1;
    panner.maxDistance = 100;
    panner.rolloffFactor = 1;

    // Position at caster initially
    if (caster.position) {
      panner.positionX.value = caster.position.x;
      panner.positionY.value = caster.position.y;
      panner.positionZ.value = caster.position.z;
    }

    // Create gain control
    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = this.config.volume;

    // Connect nodes
    source.connect(gainNode);
    gainNode.connect(panner);
    panner.connect(this.audioContext.destination);

    // Start playback
    source.start();

    // Animate movement to target if applicable
    if (target && target.position && caster.position) {
      this.animateSpellMovement(panner, caster.position, target.position, spell.castingTime);
    }
  }

  /**
   * Play preparation sound
   */
  playPreparationSound(soundBuffer, spell, caster) {
    const source = this.audioContext.createBufferSource();
    source.buffer = soundBuffer;

    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = this.config.volume * 0.5;

    // Position at caster
    if (caster.position) {
      const panner = this.audioContext.createPanner();
      panner.positionX.value = caster.position.x;
      panner.positionY.value = caster.position.y;
      panner.positionZ.value = caster.position.z;

      source.connect(gainNode);
      gainNode.connect(panner);
      panner.connect(this.audioContext.destination);
    } else {
      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
    }

    source.start();
  }

  /**
   * Animate spell movement from caster to target
   */
  animateSpellMovement(panner, startPos, endPos, duration) {
    const startTime = this.audioContext.currentTime;
    const endTime = startTime + duration / 1000;

    const animate = () => {
      const currentTime = this.audioContext.currentTime;
      const progress = Math.min((currentTime - startTime) / (endTime - startTime), 1);

      // Smooth interpolation
      const easeProgress = this.easeInOutQuad(progress);

      panner.positionX.value = startPos.x + (endPos.x - startPos.x) * easeProgress;
      panner.positionY.value = startPos.y + (endPos.y - startPos.y) * easeProgress;
      panner.positionZ.value = startPos.z + (endPos.z - startPos.z) * easeProgress;

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }

  /**
   * Easing function for smooth movement
   */
  easeInOutQuad(t) {
    return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  }

  /**
   * Add custom spell definition
   */
  addSpellDefinition(name, definition) {
    this.spellDefinitions.set(name, definition);
    this.emit('spellAdded', { name, definition });
  }

  /**
   * Remove spell definition
   */
  removeSpellDefinition(name) {
    const removed = this.spellDefinitions.delete(name);
    if (removed) {
      this.emit('spellRemoved', { name });
    }
    return removed;
  }

  /**
   * Get metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      activeSpells: this.activeSpells.size,
      preparingSpells: this.preparationState.size,
      spellDefinitionsCount: this.spellDefinitions.size
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
          console.error(`Error in spell audio processor event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup spell audio processor
   */
  cleanup() {
    // Stop all active spells
    for (const [spellId, spell] of this.activeSpells) {
      this.activeSpells.delete(spellId);
    }

    // Stop all preparation sounds
    this.preparationState.clear();

    // Disconnect sound generators
    Object.values(this.soundGenerators).forEach(generator => {
      if (generator && generator.node) {
        generator.node.disconnect();
      }
    });

    this.eventListeners.clear();
  }
}