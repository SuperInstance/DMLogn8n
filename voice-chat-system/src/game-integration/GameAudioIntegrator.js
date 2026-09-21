/**
 * Game Audio Integrator - Integrates voice chat with game systems
 * Synchronizes combat audio, spell effects, and environmental sounds with voice chat
 */

import { CombatSoundEffects } from './CombatSoundEffects.js';
import { SpellAudioProcessor } from './SpellAudioProcessor.js';
import { AmbientSoundManager } from './AmbientSoundManager.js';

export class GameAudioIntegrator {
  constructor(config = {}) {
    this.config = {
      // Combat settings
      combatEnabled: true,
      combatSoundVolume: 0.7,
      hitSoundVariations: 5,
      criticalHitChance: 0.05,

      // Spell settings
      spellAudioEnabled: true,
      spellSoundVolume: 0.8,
      spellPreparationTime: 2000, // ms
      spellEchoEnabled: true,

      // Ambient settings
      ambientSoundsEnabled: true,
      ambientVolume: 0.3,
      dynamicAmbient: true,
      weatherEffects: true,

      // Music integration
      musicIntegrationEnabled: true,
      musicDuckingLevel: 0.3,
      combatMusicIntensity: 0.8,

      // Cross-portal sync
      crossPortalSyncEnabled: true,
      syncLatency: 100, // ms

      ...config
    };

    // Audio context (should be provided by voice chat system)
    this.audioContext = null;

    // Game audio components
    this.combatSoundEffects = null;
    this.spellAudioProcessor = null;
    this.ambientSoundManager = null;

    // Game state
    this.gameState = {
      inCombat: false,
      currentLocation: 'default',
      weatherConditions: 'clear',
      timeOfDay: 'day',
      healthLevel: 1.0,
      manaLevel: 1.0,
      activeEffects: []
    };

    // Audio mixing
    this.audioMixer = {
      masterGain: null,
      voiceGain: null,
      effectsGain: null,
      musicGain: null,
      ambientGain: null
    };

    // Event system
    this.eventListeners = new Map();

    // Performance monitoring
    this.metrics = {
      activeSounds: 0,
      audioLatency: 0,
      processingLoad: 0
    };
  }

  /**
   * Initialize the game audio integrator
   */
  async initialize(audioContext) {
    try {
      this.audioContext = audioContext;

      // Initialize audio mixer
      this.initializeAudioMixer();

      // Initialize game audio components
      this.combatSoundEffects = new CombatSoundEffects(audioContext, {
        volume: this.config.combatSoundVolume,
        hitVariations: this.config.hitSoundVariations,
        criticalChance: this.config.criticalHitChance
      });

      this.spellAudioProcessor = new SpellAudioProcessor(audioContext, {
        volume: this.config.spellSoundVolume,
        preparationTime: this.config.spellPreparationTime,
        echoEnabled: this.config.spellEchoEnabled
      });

      this.ambientSoundManager = new AmbientSoundManager(audioContext, {
        volume: this.config.ambientVolume,
        dynamicAmbient: this.config.dynamicAmbient,
        weatherEffects: this.config.weatherEffects
      });

      // Initialize components
      await this.combatSoundEffects.initialize();
      await this.spellAudioProcessor.initialize();
      await this.ambientSoundManager.initialize();

      // Set up component communication
      this.setupComponentCommunication();

      this.emit('initialized');
    } catch (error) {
      console.error('Failed to initialize game audio integrator:', error);
      throw error;
    }
  }

  /**
   * Initialize audio mixing system
   */
  initializeAudioMixer() {
    // Create master gain
    this.audioMixer.masterGain = this.audioContext.createGain();
    this.audioMixer.masterGain.gain.value = 1.0;

    // Create individual gain nodes for different audio types
    this.audioMixer.voiceGain = this.audioContext.createGain();
    this.audioMixer.voiceGain.gain.value = 1.0;

    this.audioMixer.effectsGain = this.audioContext.createGain();
    this.audioMixer.effectsGain.gain.value = this.config.combatSoundVolume;

    this.audioMixer.musicGain = this.audioContext.createGain();
    this.audioMixer.musicGain.gain.value = 0.5;

    this.audioMixer.ambientGain = this.audioContext.createGain();
    this.audioMixer.ambientGain.gain.value = this.config.ambientVolume;

    // Create limiter to prevent clipping
    const limiter = this.audioContext.createDynamicsCompressor();
    limiter.threshold.value = -6;
    limiter.knee.value = 0;
    limiter.ratio.value = 20;
    limiter.attack.value = 0.001;
    limiter.release.value = 0.1;

    // Connect mixer nodes
    this.audioMixer.voiceGain.connect(this.audioMixer.masterGain);
    this.audioMixer.effectsGain.connect(this.audioMixer.masterGain);
    this.audioMixer.musicGain.connect(this.audioMixer.masterGain);
    this.audioMixer.ambientGain.connect(this.audioMixer.masterGain);

    this.audioMixer.masterGain.connect(limiter);
    limiter.connect(this.audioContext.destination);
  }

  /**
   * Set up communication between components
   */
  setupComponentCommunication() {
    // Combat sound events
    this.combatSoundEffects.on('soundPlayed', this.handleCombatSoundPlayed.bind(this));
    this.combatSoundEffects.on('combatStateChanged', this.handleCombatStateChanged.bind(this));

    // Spell audio events
    this.spellAudioProcessor.on('spellCast', this.handleSpellCast.bind(this));
    this.spellAudioProcessor.on('spellPrepared', this.handleSpellPrepared.bind(this));

    // Ambient sound events
    this.ambientSoundManager.on('ambientChanged', this.handleAmbientChanged.bind(this));
    this.ambientSoundManager.on('weatherChanged', this.handleWeatherChanged.bind(this));
  }

  /**
   * Handle combat sound events
   */
  handleCombatSoundPlayed(event) {
    const { soundType, participants, intensity } = event;

    // Duck other audio during intense combat
    if (intensity > 0.7) {
      this.duckAudio('combat', intensity);
    }

    // Sync with voice chat participants
    this.syncWithParticipants(participants);

    this.emit('combatSoundPlayed', event);
  }

  /**
   * Handle combat state changes
   */
  handleCombatStateChanged(event) {
    const { inCombat, intensity, participants } = event;

    this.gameState.inCombat = inCombat;

    if (inCombat) {
      // Increase music intensity
      this.setMusicIntensity(this.config.combatMusicIntensity);

      // Adjust ambient sounds for combat
      this.ambientSoundManager.setCombatMode(true);
    } else {
      // Return to normal music
      this.setMusicIntensity(0.5);

      // Normal ambient sounds
      this.ambientSoundManager.setCombatMode(false);
    }

    this.emit('combatStateChanged', event);
  }

  /**
   * Handle spell casting events
   */
  handleSpellCast(event) {
    const { spell, caster, target, duration } = event;

    // Create spatial audio effect for spell
    this.createSpellSpatialEffect(spell, caster, target);

    // Apply spell effects to participants
    this.applySpellEffects(spell, [caster, target]);

    // Update game state
    this.updateGameStateFromSpell(spell, caster);

    this.emit('spellCast', event);
  }

  /**
   * Handle spell preparation events
   */
  handleSpellPrepared(event) {
    const { spell, caster, preparationTime } = event;

    // Create preparation audio cues
    this.createSpellPreparationEffect(spell, caster, preparationTime);

    this.emit('spellPrepared', event);
  }

  /**
   * Handle ambient sound changes
   */
  handleAmbientChanged(event) {
    const { location, ambientType, volume } = event;

    this.gameState.currentLocation = location;

    // Adjust voice processing based on environment
    this.adjustVoiceForEnvironment(ambientType);

    this.emit('ambientChanged', event);
  }

  /**
   * Handle weather changes
   */
  handleWeatherChanged(event) {
    const { weather, intensity } = event;

    this.gameState.weatherConditions = weather;

    // Apply weather effects to voice
    this.applyWeatherEffectsToVoice(weather, intensity);

    this.emit('weatherChanged', event);
  }

  /**
   * Create spatial audio effect for spell
   */
  createSpellSpatialEffect(spell, caster, target) {
    if (!this.audioContext) return;

    // Create spell sound with spatial positioning
    const spellSound = this.spellAudioProcessor.createSpellSound(spell);

    // Position sound at caster location initially
    if (caster.position) {
      // Apply spatial positioning
      this.positionSpellSound(spellSound, caster.position, target.position);
    }

    // Connect to effects mixer
    spellSound.connect(this.audioMixer.effectsGain);
  }

  /**
   * Position spell sound in 3D space
   */
  positionSpellSound(sound, casterPos, targetPos) {
    // Create panner for spatial positioning
    const panner = this.audioContext.createPanner();
    panner.panningModel = 'HRTF';
    panner.distanceModel = 'inverse';
    panner.refDistance = 1;
    panner.maxDistance = 100;
    panner.rolloffFactor = 1;
    panner.coneInnerAngle = 360;
    panner.coneOuterAngle = 360;
    panner.coneOuterGain = 0;

    // Set position at caster
    panner.positionX.value = casterPos.x || 0;
    panner.positionY.value = casterPos.y || 0;
    panner.positionZ.value = casterPos.z || 0;

    // Create movement from caster to target
    if (targetPos) {
      this.animateSpellMovement(panner, casterPos, targetPos, 2000); // 2 second travel time
    }

    // Connect nodes
    sound.connect(panner);
    panner.connect(this.audioMixer.effectsGain);
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

      // Interpolate position
      panner.positionX.value = startPos.x + (endPos.x - startPos.x) * progress;
      panner.positionY.value = startPos.y + (endPos.y - startPos.y) * progress;
      panner.positionZ.value = startPos.z + (endPos.z - startPos.z) * progress;

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }

  /**
   * Create spell preparation effect
   */
  createSpellPreparationEffect(spell, caster, preparationTime) {
    // Create low-frequency humming sound
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.frequency.value = this.getSpellFrequency(spell);
    oscillator.type = 'sine';

    // Fade in and out
    const currentTime = this.audioContext.currentTime;
    gainNode.gain.setValueAtTime(0, currentTime);
    gainNode.gain.linearRampToValueAtTime(0.3, currentTime + 0.1);
    gainNode.gain.linearRampToValueAtTime(0.3, currentTime + preparationTime / 1000 - 0.1);
    gainNode.gain.linearRampToValueAtTime(0, currentTime + preparationTime / 1000);

    // Position at caster
    const panner = this.audioContext.createPanner();
    if (caster.position) {
      panner.positionX.value = caster.position.x;
      panner.positionY.value = caster.position.y;
      panner.positionZ.value = caster.position.z;
    }

    // Connect and play
    oscillator.connect(gainNode);
    gainNode.connect(panner);
    panner.connect(this.audioMixer.effectsGain);

    oscillator.start(currentTime);
    oscillator.stop(currentTime + preparationTime / 1000);
  }

  /**
   * Get spell frequency for preparation sound
   */
  getSpellFrequency(spell) {
    const spellFrequencies = {
      fire: 150,
      water: 200,
      earth: 100,
      air: 250,
      lightning: 300,
      healing: 400,
      necromancy: 80,
      illusion: 350
    };

    return spellFrequencies[spell.school] || 200;
  }

  /**
   * Apply spell effects to participants
   */
  applySpellEffects(spell, participants) {
    participants.forEach(participant => {
      if (!participant) return;

      // Apply voice modulation based on spell effects
      this.applySpellVoiceEffect(participant, spell);

      // Update participant state
      if (participant.updateState) {
        participant.updateState({
          activeSpell: spell,
          spellDuration: spell.duration || 5000
        });
      }
    });
  }

  /**
   * Apply spell voice effects
   */
  applySpellVoiceEffect(participant, spell) {
    const voiceEffects = {
      fire: { pitch: 0.2, distortion: 0.3 },
      water: { pitch: -0.1, reverb: 0.4 },
      earth: { pitch: -0.3, lowPass: 800 },
      air: { pitch: 0.1, highPass: 200 },
      lightning: { pitch: 0.4, static: 0.5 },
      healing: { pitch: 0.1, chorus: 0.3 },
      necromancy: { pitch: -0.4, echo: 0.6 },
      illusion: { pitch: 0.3, phase: 0.4 }
    };

    const effect = voiceEffects[spell.school];
    if (effect && participant.applyVoiceEffect) {
      participant.applyVoiceEffect(effect, spell.duration || 5000);
    }
  }

  /**
   * Update game state from spell
   */
  updateGameStateFromSpell(spell, caster) {
    // Update mana level
    if (spell.manaCost) {
      this.gameState.manaLevel = Math.max(0, this.gameState.manaLevel - spell.manaCost);
    }

    // Add active effect
    this.gameState.activeEffects.push({
      type: 'spell',
      spell: spell.name,
      caster: caster.id,
      startTime: Date.now(),
      duration: spell.duration || 5000
    });

    this.emit('gameStateUpdated', this.gameState);
  }

  /**
   * Add combat sound effects
   */
  addCombatSoundEffects(effects, participants) {
    if (!this.config.combatEnabled || !this.combatSoundEffects) return;

    effects.forEach(effect => {
      this.combatSoundEffects.playSound(effect.type, {
        participants,
        intensity: effect.intensity,
        position: effect.position
      });
    });
  }

  /**
   * Add spell audio
   */
  addSpellAudio(spell, caster, target) {
    if (!this.config.spellAudioEnabled || !this.spellAudioProcessor) return;

    this.spellAudioProcessor.castSpell(spell, caster, target);
  }

  /**
   * Duck audio for important events
   */
  duckAudio(reason, intensity) {
    const duckingAmount = intensity * this.config.musicDuckingLevel;

    switch (reason) {
      case 'combat':
        this.audioMixer.musicGain.gain.value = 0.5 * (1 - duckingAmount);
        this.audioMixer.ambientGain.gain.value = this.config.ambientVolume * (1 - duckingAmount);
        break;
      case 'spell':
        this.audioMixer.musicGain.gain.value = 0.5 * (1 - duckingAmount * 0.5);
        break;
    }

    // Gradually restore audio after ducking
    setTimeout(() => {
      this.restoreAudioLevels();
    }, 1000);
  }

  /**
   * Restore normal audio levels
   */
  restoreAudioLevels() {
    this.audioMixer.musicGain.gain.linearRampToValueAtTime(
      0.5,
      this.audioContext.currentTime + 0.5
    );
    this.audioMixer.ambientGain.gain.linearRampToValueAtTime(
      this.config.ambientVolume,
      this.audioContext.currentTime + 0.5
    );
  }

  /**
   * Sync audio with participants
   */
  syncWithParticipants(participants) {
    if (!this.config.crossPortalSyncEnabled) return;

    participants.forEach(participant => {
      if (participant.audioLatency) {
        // Compensate for participant audio latency
        this.compensateForLatency(participant, participant.audioLatency);
      }
    });
  }

  /**
   * Compensate for audio latency
   */
  compensateForLatency(participant, latency) {
    // Apply delay compensation
    const delayCompensation = this.audioContext.createDelay(2.0);
    delayCompensation.delayTime.value = latency / 1000;

    // This would be integrated into the participant's audio chain
    if (participant.audioChain) {
      // Insert delay compensation into audio chain
    }
  }

  /**
   * Adjust voice for environment
   */
  adjustVoiceForEnvironment(environmentType) {
    const environmentEffects = {
      cave: { reverb: 0.8, echo: 0.3, lowPass: 6000 },
      forest: { reverb: 0.2, highPass: 100, chorus: 0.1 },
      dungeon: { reverb: 0.6, echo: 0.4, lowPass: 4000 },
      outdoor: { reverb: 0.1, brightness: 1.2 },
      indoor: { reverb: 0.4, warmth: 1.1 },
      underwater: { lowPass: 800, bubbles: true }
    };

    const effect = environmentEffects[environmentType];
    if (effect) {
      this.emit('environmentVoiceEffect', { environmentType, effect });
    }
  }

  /**
   * Apply weather effects to voice
   */
  applyWeatherEffectsToVoice(weather, intensity) {
    const weatherEffects = {
      rain: { noise: 0.3, lowPass: 7000 },
      wind: { noise: 0.2, modulation: 0.4 },
      storm: { noise: 0.5, thunder: true, lowPass: 5000 },
      snow: { noise: 0.1, highPass: 150 },
      fog: { muffled: true, brightness: 0.8 }
    };

    const effect = weatherEffects[weather];
    if (effect) {
      this.emit('weatherVoiceEffect', { weather, intensity, effect });
    }
  }

  /**
   * Set music intensity
   */
  setMusicIntensity(intensity) {
    this.audioMixer.musicGain.gain.linearRampToValueAtTime(
      intensity,
      this.audioContext.currentTime + 1.0
    );

    this.emit('musicIntensityChanged', { intensity });
  }

  /**
   * Update game state
   */
  updateGameState(newState) {
    Object.assign(this.gameState, newState);
    this.emit('gameStateUpdated', this.gameState);
  }

  /**
   * Get current game state
   */
  getGameState() {
    return { ...this.gameState };
  }

  /**
   * Get performance metrics
   */
  getMetrics() {
    const componentMetrics = {
      combat: this.combatSoundEffects?.getMetrics() || {},
      spells: this.spellAudioProcessor?.getMetrics() || {},
      ambient: this.ambientSoundManager?.getMetrics() || {}
    };

    return {
      ...this.metrics,
      components: componentMetrics,
      gameState: this.gameState,
      audioLevels: {
        voice: this.audioMixer.voiceGain.gain.value,
        effects: this.audioMixer.effectsGain.gain.value,
        music: this.audioMixer.musicGain.gain.value,
        ambient: this.audioMixer.ambientGain.gain.value
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
          console.error(`Error in game audio integrator event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup and destroy game audio integrator
   */
  cleanup() {
    // Cleanup components
    if (this.combatSoundEffects) {
      this.combatSoundEffects.cleanup();
    }
    if (this.spellAudioProcessor) {
      this.spellAudioProcessor.cleanup();
    }
    if (this.ambientSoundManager) {
      this.ambientSoundManager.cleanup();
    }

    // Disconnect mixer nodes
    Object.values(this.audioMixer).forEach(node => {
      if (node && node.disconnect) {
        node.disconnect();
      }
    });

    // Clear event listeners
    this.eventListeners.clear();
  }
}