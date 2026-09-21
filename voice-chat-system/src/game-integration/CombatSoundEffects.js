/**
 * Combat Sound Effects - Handles all combat-related audio
 * Provides hit sounds, weapon effects, armor sounds, and combat ambience
 */

export class CombatSoundEffects {
  constructor(audioContext, config = {}) {
    this.audioContext = audioContext;
    this.config = {
      volume: 0.7,
      hitVariations: 5,
      criticalHitChance: 0.05,
      weaponSoundsEnabled: true,
      armorSoundsEnabled: true,
      environmentalHits: true,
      ...config
    };

    // Sound libraries
    this.soundLibrary = {
      hits: [],
      weaponSwings: [],
      armorHits: [],
      environmentalHits: [],
      combatAmbience: []
    };

    // Combat state
    this.combatState = {
      inCombat: false,
      intensity: 0,
      participants: new Set(),
      lastHitTime: 0
    };

    // Active sounds
    this.activeSounds = new Map();

    // Event system
    this.eventListeners = new Map();

    // Performance monitoring
    this.metrics = {
      hitsPlayed: 0,
      criticalHits: 0,
      averageIntensity: 0,
      soundsPlaying: 0
    };
  }

  /**
   * Initialize combat sound effects
   */
  async initialize() {
    try {
      // Generate procedural combat sounds
      await this.generateCombatSounds();

      // Set up performance monitoring
      this.startPerformanceMonitoring();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize combat sound effects:', error);
      throw error;
    }
  }

  /**
   * Generate procedural combat sounds
   */
  async generateCombatSounds() {
    // Generate hit sounds
    for (let i = 0; i < this.config.hitVariations; i++) {
      this.soundLibrary.hits.push(await this.generateHitSound(i));
    }

    // Generate weapon swing sounds
    for (let i = 0; i < 3; i++) {
      this.soundLibrary.weaponSwings.push(await this.generateWeaponSwing(i));
    }

    // Generate armor hit sounds
    for (let i = 0; i < 4; i++) {
      this.soundLibrary.armorHits.push(await this.generateArmorHit(i));
    }

    // Generate environmental hit sounds
    for (let i = 0; i < 3; i++) {
      this.soundLibrary.environmentalHits.push(await this.generateEnvironmentalHit(i));
    }

    // Generate combat ambience
    this.soundLibrary.combatAmbience.push(await this.generateCombatAmbience());
  }

  /**
   * Generate hit sound
   */
  async generateHitSound(variation) {
    const duration = 0.1 + Math.random() * 0.2; // 100-300ms
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);

    for (let channel = 0; channel < 2; channel++) {
      const channelData = buffer.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        const time = i / sampleRate;

        // Create impact sound with multiple components
        let sample = 0;

        // Initial transient (sharp attack)
        const transient = Math.exp(-time * 50) * (Math.random() - 0.5) * 2;
        sample += transient * (0.8 + variation * 0.1);

        // Body resonance (lower frequency)
        const resonance = Math.sin(2 * Math.PI * 80 * time) * Math.exp(-time * 10);
        sample += resonance * 0.5;

        // Click/crack component
        const click = Math.sin(2 * Math.PI * 2000 * time) * Math.exp(-time * 100) * 0.3;
        sample += click * (1 - variation * 0.2);

        // Add some noise for texture
        const noise = (Math.random() - 0.5) * 0.1 * Math.exp(-time * 30);
        sample += noise;

        channelData[i] = sample * this.config.volume;
      }
    }

    return buffer;
  }

  /**
   * Generate weapon swing sound
   */
  async generateWeaponSwing(variation) {
    const duration = 0.3 + variation * 0.1;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);

    for (let channel = 0; channel < 2; channel++) {
      const channelData = buffer.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        const time = i / sampleRate;

        // Create whoosh/swing sound
        let sample = 0;

        // Wind noise component
        const windNoise = (Math.random() - 0.5) * 0.8;
        sample += windNoise;

        // Low frequency whoosh
        const whoosh = Math.sin(2 * Math.PI * 40 * time) * Math.exp(-time * 3);
        sample += whoosh * 0.6;

        // High frequency sizzle
        const sizzle = Math.sin(2 * Math.PI * 3000 * time) * Math.exp(-time * 20);
        sample += sizzle * 0.2;

        // Apply envelope (quick fade in, slower fade out)
        const envelope = time < 0.05 ? time / 0.05 : Math.exp(-(time - 0.05) * 5);
        sample *= envelope;

        channelData[i] = sample * this.config.volume * 0.5;
      }
    }

    return buffer;
  }

  /**
   * Generate armor hit sound
   */
  async generateArmorHit(variation) {
    const duration = 0.15 + variation * 0.05;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);

    for (let channel = 0; channel < 2; channel++) {
      const channelData = buffer.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        const time = i / sampleRate;

        // Create metallic clank sound
        let sample = 0;

        // Metallic impact
        const impact = Math.sin(2 * Math.PI * 1500 * time) * Math.exp(-time * 30);
        sample += impact * 0.8;

        // Resonance (metal ring)
        const resonance = Math.sin(2 * Math.PI * 800 * time) * Math.exp(-time * 5);
        sample += resonance * 0.6;

        // High frequency shimmer
        const shimmer = Math.sin(2 * Math.PI * 4000 * time) * Math.exp(-time * 50);
        sample += shimmer * 0.3;

        // Metallic noise
        const noise = (Math.random() - 0.5) * 0.2 * Math.exp(-time * 20);
        sample += noise;

        channelData[i] = sample * this.config.volume * 0.7;
      }
    }

    return buffer;
  }

  /**
   * Generate environmental hit sound
   */
  async generateEnvironmentalHit(variation) {
    const duration = 0.2 + variation * 0.1;
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);

    for (let channel = 0; channel < 2; channel++) {
      const channelData = buffer.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        const time = i / sampleRate;

        // Create environmental impact sound
        let sample = 0;

        // Low frequency thud
        const thud = Math.sin(2 * Math.PI * 60 * time) * Math.exp(-time * 8);
        sample += thud;

        // Debris scatter
        const debris = (Math.random() - 0.5) * 0.4 * Math.exp(-time * 15);
        sample += debris;

        // Dust/rock noise
        const dustNoise = (Math.random() - 0.5) * 0.3 * Math.exp(-time * 25);
        sample += dustNoise;

        channelData[i] = sample * this.config.volume * 0.4;
      }
    }

    return buffer;
  }

  /**
   * Generate combat ambience
   */
  async generateCombatAmbience() {
    const duration = 10; // 10 seconds of ambience
    const sampleRate = this.audioContext.sampleRate;
    const buffer = this.audioContext.createBuffer(2, duration * sampleRate, sampleRate);

    for (let channel = 0; channel < 2; channel++) {
      const channelData = buffer.getChannelData(channel);

      for (let i = 0; i < channelData.length; i++) {
        const time = i / sampleRate;

        // Create combat atmosphere
        let sample = 0;

        // Low rumble
        const rumble = (Math.random() - 0.5) * 0.1;
        sample += rumble;

        // Occasional distant sounds
        if (Math.random() < 0.001) {
          sample += (Math.random() - 0.5) * 0.3;
        }

        // Wind/tension
        const tension = Math.sin(2 * Math.PI * 20 * time) * 0.05;
        sample += tension;

        channelData[i] = sample * this.config.volume * 0.2;
      }
    }

    return buffer;
  }

  /**
   * Play a combat sound
   */
  playSound(soundType, options = {}) {
    const { participants = [], intensity = 0.5, position = null } = options;

    try {
      let soundBuffer = null;

      // Select appropriate sound
      switch (soundType) {
        case 'hit':
          soundBuffer = this.getRandomHitSound();
          break;
        case 'criticalHit':
          soundBuffer = this.getRandomHitSound();
          intensity = 1.0;
          break;
        case 'weaponSwing':
          soundBuffer = this.getRandomWeaponSwing();
          break;
        case 'armorHit':
          soundBuffer = this.getRandomArmorHit();
          break;
        case 'environmentalHit':
          soundBuffer = this.getRandomEnvironmentalHit();
          break;
        case 'combatAmbience':
          soundBuffer = this.getRandomCombatAmbience();
          break;
        default:
          console.warn(`Unknown combat sound type: ${soundType}`);
          return;
      }

      if (!soundBuffer) return;

      // Create and play sound
      this.playCombatSound(soundBuffer, soundType, intensity, position);

      // Update metrics
      this.updateMetrics(soundType, intensity);

      // Emit sound played event
      this.emit('soundPlayed', {
        soundType,
        participants,
        intensity,
        position,
        timestamp: Date.now()
      });

    } catch (error) {
      console.error('Failed to play combat sound:', error);
    }
  }

  /**
   * Get random hit sound
   */
  getRandomHitSound() {
    const index = Math.floor(Math.random() * this.soundLibrary.hits.length);
    return this.soundLibrary.hits[index];
  }

  /**
   * Get random weapon swing sound
   */
  getRandomWeaponSwing() {
    const index = Math.floor(Math.random() * this.soundLibrary.weaponSwings.length);
    return this.soundLibrary.weaponSwings[index];
  }

  /**
   * Get random armor hit sound
   */
  getRandomArmorHit() {
    const index = Math.floor(Math.random() * this.soundLibrary.armorHits.length);
    return this.soundLibrary.armorHits[index];
  }

  /**
   * Get random environmental hit sound
   */
  getRandomEnvironmentalHit() {
    const index = Math.floor(Math.random() * this.soundLibrary.environmentalHits.length);
    return this.soundLibrary.environmentalHits[index];
  }

  /**
   * Get random combat ambience
   */
  getRandomCombatAmbience() {
    const index = Math.floor(Math.random() * this.soundLibrary.combatAmbience.length);
    return this.soundLibrary.combatAmbience[index];
  }

  /**
   * Play combat sound with spatial positioning
   */
  playCombatSound(soundBuffer, soundType, intensity, position) {
    const source = this.audioContext.createBufferSource();
    source.buffer = soundBuffer;

    // Create gain node for volume control
    const gainNode = this.audioContext.createGain();
    gainNode.gain.value = intensity * this.config.volume;

    // Create spatial positioning if position is provided
    if (position) {
      const panner = this.audioContext.createPanner();
      panner.panningModel = 'HRTF';
      panner.distanceModel = 'inverse';
      panner.refDistance = 1;
      panner.maxDistance = 50;
      panner.rolloffFactor = 1;

      panner.positionX.value = position.x;
      panner.positionY.value = position.y;
      panner.positionZ.value = position.z;

      // Connect nodes
      source.connect(gainNode);
      gainNode.connect(panner);
      panner.connect(this.audioContext.destination);
    } else {
      // No spatial positioning
      source.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
    }

    // Store active sound
    const soundId = `${soundType}_${Date.now()}_${Math.random()}`;
    this.activeSounds.set(soundId, {
      source,
      gainNode,
      startTime: this.audioContext.currentTime,
      type: soundType
    });

    // Start and cleanup
    source.start();
    source.onended = () => {
      this.activeSounds.delete(soundId);
      this.metrics.soundsPlaying = this.activeSounds.size;
    };

    this.metrics.soundsPlaying = this.activeSounds.size;
  }

  /**
   * Start combat mode
   */
  startCombat(participants = []) {
    this.combatState.inCombat = true;
    this.combatState.participants = new Set(participants);
    this.combatState.intensity = 0.5;

    // Start combat ambience
    this.playSound('combatAmbience', { intensity: 0.3 });

    this.emit('combatStateChanged', {
      inCombat: true,
      participants,
      intensity: this.combatState.intensity
    });
  }

  /**
   * Stop combat mode
   */
  stopCombat() {
    this.combatState.inCombat = false;
    this.combatState.intensity = 0;
    this.combatState.participants.clear();

    // Fade out combat sounds
    this.fadeOutCombatSounds();

    this.emit('combatStateChanged', {
      inCombat: false,
      participants: [],
      intensity: 0
    });
  }

  /**
   * Fade out combat sounds
   */
  fadeOutCombatSounds() {
    const fadeTime = 1.0; // 1 second fade

    for (const [soundId, sound] of this.activeSounds) {
      if (sound.type === 'combatAmbience') {
        sound.gainNode.gain.linearRampToValueAtTime(
          0,
          this.audioContext.currentTime + fadeTime
        );
      }
    }
  }

  /**
   * Update combat intensity
   */
  updateIntensity(intensity) {
    this.combatState.intensity = Math.max(0, Math.min(1, intensity));

    // Adjust ambience volume based on intensity
    for (const [soundId, sound] of this.activeSounds) {
      if (sound.type === 'combatAmbience') {
        sound.gainNode.gain.value = this.combatState.intensity * 0.3 * this.config.volume;
      }
    }

    this.emit('intensityChanged', { intensity: this.combatState.intensity });
  }

  /**
   * Process combat event
   */
  processCombatEvent(event) {
    const { type, attacker, defender, damage, critical } = event;

    switch (type) {
      case 'meleeAttack':
        this.playSound('weaponSwing', {
          participants: [attacker, defender],
          position: defender.position
        });

        setTimeout(() => {
          if (critical) {
            this.playSound('criticalHit', {
              participants: [defender],
              intensity: 1.0,
              position: defender.position
            });
            this.metrics.criticalHits++;
          } else {
            this.playSound('hit', {
              participants: [defender],
              intensity: Math.min(1.0, damage / 20),
              position: defender.position
            });
          }
        }, 100); // Small delay for impact

        if (defender.armor && this.config.armorSoundsEnabled) {
          setTimeout(() => {
            this.playSound('armorHit', {
              participants: [defender],
              intensity: 0.6,
              position: defender.position
            });
          }, 50);
        }
        break;

      case 'rangedAttack':
        this.playSound('weaponSwing', {
          participants: [attacker],
          position: attacker.position
        });

        setTimeout(() => {
          this.playSound('hit', {
            participants: [defender],
            intensity: Math.min(1.0, damage / 15),
            position: defender.position
          });
        }, 200); // Travel time for projectile
        break;

      case 'environmentalDamage':
        this.playSound('environmentalHit', {
          participants: [defender],
          intensity: 0.7,
          position: event.position
        });
        break;
    }

    this.combatState.lastHitTime = Date.now();
    this.metrics.hitsPlayed++;
  }

  /**
   * Update performance metrics
   */
  updateMetrics(soundType, intensity) {
    this.metrics.averageIntensity =
      (this.metrics.averageIntensity + intensity) / 2;
  }

  /**
   * Start performance monitoring
   */
  startPerformanceMonitoring() {
    setInterval(() => {
      this.metrics.soundsPlaying = this.activeSounds.size;
      this.metrics.averageIntensity = this.combatState.intensity;
    }, 1000);
  }

  /**
   * Get metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      combatState: { ...this.combatState },
      soundLibrarySizes: {
        hits: this.soundLibrary.hits.length,
        weaponSwings: this.soundLibrary.weaponSwings.length,
        armorHits: this.soundLibrary.armorHits.length,
        environmentalHits: this.soundLibrary.environmentalHits.length,
        combatAmbience: this.soundLibrary.combatAmbience.length
      }
    };
  }

  /**
   * Set volume
   */
  setVolume(volume) {
    this.config.volume = Math.max(0, Math.min(1, volume));

    // Update existing sounds
    for (const [soundId, sound] of this.activeSounds) {
      sound.gainNode.gain.value = sound.gainNode.gain.value * (this.config.volume / volume);
    }

    this.emit('volumeChanged', { volume: this.config.volume });
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
          console.error(`Error in combat sound effects event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup combat sound effects
   */
  cleanup() {
    // Stop all active sounds
    for (const [soundId, sound] of this.activeSounds) {
      try {
        sound.source.stop();
        sound.source.disconnect();
        sound.gainNode.disconnect();
      } catch (error) {
        // Sound might have already ended
      }
    }

    this.activeSounds.clear();
    this.soundLibrary = {};
    this.eventListeners.clear();
  }
}