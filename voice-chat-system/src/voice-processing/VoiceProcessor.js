/**
 * Voice Processor - Handles voice processing, character customization, and advanced features
 * Provides noise suppression, echo cancellation, voice activity detection, and character voice filters
 */

import { VoiceActivityDetector } from './VoiceActivityDetector.js';
import { NoiseSuppressor } from './NoiseSuppressor.js';
import { CharacterVoiceFilter } from './CharacterVoiceFilter.js';
import { SpeechTranscriber } from './SpeechTranscriber.js';

export class VoiceProcessor {
  constructor(audioContext, config = {}) {
    this.audioContext = audioContext;
    this.config = {
      // Audio processing settings
      sampleRate: audioContext.sampleRate,
      bufferSize: 4096,
      channelCount: 2,

      // Voice processing features
      noiseSuppression: true,
      echoCancellation: true,
      autoGainControl: true,
      voiceActivityDetection: true,
      compressionEnabled: true,

      // Character voice settings
      characterVoices: {
        dwarvish: { pitch: -0.3, formantShift: 0.8, resonance: 1.2, roughness: 0.4 },
        elvish: { pitch: 0.2, formantShift: 1.1, resonance: 0.9, roughness: 0.1 },
        orcish: { pitch: -0.5, formantShift: 0.7, resonance: 1.4, roughness: 0.8 },
        human: { pitch: 0, formantShift: 1.0, resonance: 1.0, roughness: 0.2 },
        draconic: { pitch: 0.4, formantShift: 1.3, resonance: 1.1, roughness: 0.3 },
        halfling: { pitch: 0.3, formantShift: 1.15, resonance: 0.95, roughness: 0.15 },
        gnome: { pitch: 0.5, formantShift: 1.2, resonance: 0.85, roughness: 0.1 },
        undead: { pitch: -0.8, formantShift: 0.6, resonance: 1.6, roughness: 0.9 }
      },

      // Voice aging effects
      ageEffects: {
        young: { pitch: 0.2, formantShift: 1.1, clarity: 1.2 },
        adult: { pitch: 0, formantShift: 1.0, clarity: 1.0 },
        middle: { pitch: -0.1, formantShift: 0.95, clarity: 0.9 },
        old: { pitch: -0.3, formantShift: 0.85, clarity: 0.7 },
        ancient: { pitch: -0.5, formantShift: 0.7, clarity: 0.5 }
      },

      // Emotion-based modulation
      emotions: {
        neutral: { pitchVariation: 0.1, tempo: 1.0, volume: 1.0 },
        happy: { pitchVariation: 0.3, tempo: 1.1, volume: 1.2 },
        sad: { pitchVariation: 0.05, tempo: 0.9, volume: 0.8 },
        angry: { pitchVariation: 0.4, tempo: 1.2, volume: 1.4 },
        fearful: { pitchVariation: 0.6, tempo: 1.3, volume: 0.9 },
        excited: { pitchVariation: 0.5, tempo: 1.4, volume: 1.3 }
      },

      ...config
    };

    // Voice processing components
    this.voiceActivityDetector = null;
    this.noiseSuppressor = null;
    this.characterVoiceFilter = null;
    this.speechTranscriber = null;

    // Audio processing chain
    this.processingChain = {
      input: null,
      noiseGate: null,
      highPass: null,
      lowPass: null,
      compressor: null,
      pitchShifter: null,
      formantShifter: null,
      resonanceFilter: null,
      output: null
    };

    // Voice state
    this.voiceState = {
      isActive: false,
      level: 0,
      pitch: 0,
      formants: [],
      character: 'human',
      age: 'adult',
      emotion: 'neutral',
      isMuted: false,
      isProcessing: false
    };

    // Audio worklets
    this.workletProcessors = new Map();

    // Event system
    this.eventListeners = new Map();

    // Performance monitoring
    this.metrics = {
      processingLatency: 0,
      cpuUsage: 0,
      noiseLevel: 0,
      voiceQuality: 1.0
    };

    // Initialize components
    this.initializeComponents();
  }

  /**
   * Initialize voice processing components
   */
  initializeComponents() {
    // Initialize voice activity detector
    if (this.config.voiceActivityDetection) {
      this.voiceActivityDetector = new VoiceActivityDetector(this.audioContext, {
        threshold: 0.01,
        attackTime: 0.01,
        releaseTime: 0.1
      });

      this.voiceActivityDetector.on('voiceActivity', this.handleVoiceActivity.bind(this));
    }

    // Initialize noise suppressor
    if (this.config.noiseSuppression) {
      this.noiseSuppressor = new NoiseSuppressor(this.audioContext, {
        spectralSubtraction: true,
        gateThreshold: -40,
        reductionAmount: 0.8
      });
    }

    // Initialize character voice filter
    this.characterVoiceFilter = new CharacterVoiceFilter(
      this.audioContext,
      this.config.characterVoices
    );

    // Initialize speech transcriber
    this.speechTranscriber = new SpeechTranscriber({
      language: 'en-US',
      continuous: true,
      interimResults: true
    });

    this.speechTranscriber.on('transcription', this.handleTranscription.bind(this));
  }

  /**
   * Process local audio stream
   */
  async processLocalStream(stream) {
    try {
      // Create media stream source
      const source = this.audioContext.createMediaStreamSource(stream);

      // Create processing chain
      await this.createProcessingChain(source);

      // Create output stream
      const outputStream = this.createOutputStream();

      // Start voice activity detection
      if (this.voiceActivityDetector) {
        this.voiceActivityDetector.start(stream);
      }

      this.voiceState.isProcessing = true;
      this.emit('processingStarted', { inputStream: stream, outputStream });

      return outputStream;
    } catch (error) {
      console.error('Failed to process local stream:', error);
      throw error;
    }
  }

  /**
   * Create audio processing chain
   */
  async createProcessingChain(source) {
    // Create processing nodes
    this.processingChain.input = source;

    // Noise gate
    this.processingChain.noiseGate = this.audioContext.createGain();
    this.processingChain.noiseGate.gain.value = 0;

    // High-pass filter for plosive removal
    this.processingChain.highPass = this.audioContext.createBiquadFilter();
    this.processingChain.highPass.type = 'highpass';
    this.processingChain.highPass.frequency.value = 80;
    this.processingChain.highPass.Q.value = 1;

    // Low-pass filter for harshness reduction
    this.processingChain.lowPass = this.audioContext.createBiquadFilter();
    this.processingChain.lowPass.type = 'lowpass';
    this.processingChain.lowPass.frequency.value = 8000;
    this.processingChain.lowPass.Q.value = 1;

    // Compressor for dynamics control
    this.processingChain.compressor = this.audioContext.createDynamicsCompressor();
    this.processingChain.compressor.threshold.value = -24;
    this.processingChain.compressor.knee.value = 8;
    this.processingChain.compressor.ratio.value = 4;
    this.processingChain.compressor.attack.value = 0.01;
    this.processingChain.compressor.release.value = 0.25;

    // Load audio worklets for advanced processing
    await this.loadVoiceProcessingWorklets();

    // Connect processing chain
    source.connect(this.processingChain.highPass);
    this.processingChain.highPass.connect(this.processingChain.lowPass);
    this.processingChain.lowPass.connect(this.processingChain.compressor);

    // Apply noise suppression if enabled
    if (this.noiseSuppressor) {
      const noiseProcessor = await this.noiseSuppressor.createProcessor();
      this.processingChain.compressor.connect(noiseProcessor);
      noiseProcessor.connect(this.processingChain.noiseGate);
    } else {
      this.processingChain.compressor.connect(this.processingChain.noiseGate);
    }

    // Apply character voice filtering
    this.applyCharacterVoiceFilter();
  }

  /**
   * Load voice processing audio worklets
   */
  async loadVoiceProcessingWorklets() {
    const worklets = [
      'pitch-shifter.js',
      'formant-shifter.js',
      'voice-activity-detector.js',
      'spectral-noise-suppressor.js'
    ];

    for (const worklet of worklets) {
      try {
        await this.audioContext.audioWorklet.addModule(`/worklets/${worklet}`);
        this.workletProcessors.set(worklet, true);
      } catch (error) {
        console.warn(`Failed to load voice processing worklet ${worklet}:`, error);
      }
    }
  }

  /**
   * Apply character voice filter
   */
  applyCharacterVoiceFilter() {
    const characterConfig = this.config.characterVoices[this.voiceState.character];
    if (!characterConfig) return;

    // Create pitch shifter
    this.processingChain.pitchShifter = this.createPitchShifter(characterConfig.pitch);

    // Create formant shifter
    this.processingChain.formantShifter = this.createFormantShifter(characterConfig.formantShift);

    // Create resonance filter
    this.processingChain.resonanceFilter = this.createResonanceFilter(characterConfig.resonance);

    // Apply aging effects
    this.applyAgingEffects();

    // Apply emotional modulation
    this.applyEmotionalModulation();

    // Connect the character processing chain
    const lastNode = this.processingChain.noiseGate;

    if (this.processingChain.pitchShifter) {
      lastNode.connect(this.processingChain.pitchShifter);
      this.processingChain.pitchShifter.connect(this.processingChain.formantShifter || this.processingChain.output);
    }

    if (this.processingChain.formantShifter) {
      const sourceNode = this.processingChain.pitchShifter || lastNode;
      sourceNode.connect(this.processingChain.formantShifter);
      this.processingChain.formantShifter.connect(this.processingChain.resonanceFilter || this.processingChain.output);
    }

    if (this.processingChain.resonanceFilter) {
      const sourceNode = this.processingChain.formantShifter || this.processingChain.pitchShifter || lastNode;
      sourceNode.connect(this.processingChain.resonanceFilter);
      this.processingChain.resonanceFilter.connect(this.processingChain.output);
    }
  }

  /**
   * Create pitch shifter
   */
  createPitchShifter(pitchShift) {
    if (Math.abs(pitchShift) < 0.01) return null;

    // Use granular synthesis approach for pitch shifting
    const pitchShifterNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    pitchShifterNode.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);
      const outputBuffer = e.outputBuffer.getChannelData(0);

      // Simple pitch shifting using resampling (would use more sophisticated algorithm in production)
      const pitchRatio = Math.pow(2, pitchShift / 12);

      for (let i = 0; i < outputBuffer.length; i++) {
        const sourceIndex = Math.floor(i / pitchRatio);
        if (sourceIndex < inputBuffer.length) {
          outputBuffer[i] = inputBuffer[sourceIndex];
        } else {
          outputBuffer[i] = 0;
        }
      }
    };

    return pitchShifterNode;
  }

  /**
   * Create formant shifter
   */
  createFormantShifter(formantShift) {
    if (Math.abs(formantShift - 1.0) < 0.01) return null;

    // Create multiple filters for formant shifting
    const formantFilters = [];

    // Typical vowel formants (Hz)
    const formants = [
      { freq: 500, bw: 100, gain: 1.0 },  // First formant
      { freq: 1500, bw: 200, gain: 0.8 }, // Second formant
      { freq: 2500, bw: 300, gain: 0.6 }, // Third formant
      { freq: 3500, bw: 400, gain: 0.4 }  // Fourth formant
    ];

    const formantMerger = this.audioContext.createChannelMerger(formants.length);

    formants.forEach((formant, index) => {
      const filter = this.audioContext.createBiquadFilter();
      filter.type = 'bandpass';
      filter.frequency.value = formant.freq * formantShift;
      filter.Q.value = formant.freq / formant.bw;

      const gainNode = this.audioContext.createGain();
      gainNode.gain.value = formant.gain;

      // Connect to formant processing chain
      formantFilters.push({ filter, gainNode });
    });

    const formantShifterNode = this.audioContext.createScriptProcessor(4096, 1, formants.length);

    formantShifterNode.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);

      // Distribute input to all formant filters
      formantFilters.forEach(({ filter, gainNode }, index) => {
        const outputBuffer = e.outputBuffer.getChannelData(index);

        // Copy input to formant filter
        for (let i = 0; i < outputBuffer.length; i++) {
          outputBuffer[i] = inputBuffer[i];
        }
      });
    };

    return formantShifterNode;
  }

  /**
   * Create resonance filter
   */
  createResonanceFilter(resonance) {
    if (Math.abs(resonance - 1.0) < 0.01) return null;

    const filter = this.audioContext.createBiquadFilter();
    filter.type = 'peaking';
    filter.frequency.value = 1000;
    filter.gain.value = (resonance - 1.0) * 10; // Convert to dB
    filter.Q.value = 1.0;

    return filter;
  }

  /**
   * Apply aging effects to voice
   */
  applyAgingEffects() {
    const ageConfig = this.config.ageEffects[this.voiceState.age];
    if (!ageConfig) return;

    // Adjust pitch for age
    if (this.processingChain.pitchShifter) {
      // Combine character and age pitch adjustments
      const characterConfig = this.config.characterVoices[this.voiceState.character];
      const totalPitchShift = characterConfig.pitch + ageConfig.pitch;

      // Update pitch shifter parameters
      // (In production, would update the pitch shifter dynamically)
    }

    // Adjust formants for age
    if (this.processingChain.formantShifter) {
      const characterConfig = this.config.characterVoices[this.voiceState.character];
      const totalFormantShift = characterConfig.formantShift * ageConfig.formantShift;

      // Update formant shifter parameters
    }

    // Apply clarity filter (high-frequency boost/cut)
    const clarityFilter = this.audioContext.createBiquadFilter();
    clarityFilter.type = 'highshelf';
    clarityFilter.frequency.value = 4000;
    clarityFilter.gain.value = (ageConfig.clarity - 1.0) * 6; // Convert to dB
  }

  /**
   * Apply emotional modulation
   */
  applyEmotionalModulation() {
    const emotionConfig = this.config.emotions[this.voiceState.emotion];
    if (!emotionConfig) return;

    // Create LFO for pitch variation
    const lfo = this.audioContext.createOscillator();
    lfo.frequency.value = 5; // 5 Hz modulation

    const lfoGain = this.audioContext.createGain();
    lfoGain.gain.value = emotionConfig.pitchVariation * 50; // Convert to Hz

    // Connect LFO to pitch modulation
    lfo.connect(lfoGain);

    // Create tempo adjustment (would require time stretching)
    // Create volume adjustment
    const emotionGain = this.audioContext.createGain();
    emotionGain.gain.value = emotionConfig.volume;

    lfo.start();
  }

  /**
   * Create output stream from processed audio
   */
  createOutputStream() {
    const destination = this.audioContext.createMediaStreamDestination();

    // Connect final output node to destination
    let outputNode = this.processingChain.resonanceFilter ||
                     this.processingChain.formantShifter ||
                     this.processingChain.pitchShifter ||
                     this.processingChain.noiseGate;

    if (outputNode) {
      outputNode.connect(destination);
    }

    this.processingChain.output = destination;
    return destination.stream;
  }

  /**
   * Set character voice type
   */
  setCharacterVoice(character) {
    if (!this.config.characterVoices[character]) {
      console.warn(`Unknown character type: ${character}`);
      return;
    }

    this.voiceState.character = character;

    // Reapply character voice filter
    if (this.voiceState.isProcessing) {
      this.applyCharacterVoiceFilter();
    }

    this.emit('characterVoiceChanged', { character });
  }

  /**
   * Set voice age
   */
  setVoiceAge(age) {
    if (!this.config.ageEffects[age]) {
      console.warn(`Unknown age type: ${age}`);
      return;
    }

    this.voiceState.age = age;

    // Reapply aging effects
    if (this.voiceState.isProcessing) {
      this.applyAgingEffects();
    }

    this.emit('voiceAgeChanged', { age });
  }

  /**
   * Set emotion
   */
  setEmotion(emotion) {
    if (!this.config.emotions[emotion]) {
      console.warn(`Unknown emotion: ${emotion}`);
      return;
    }

    this.voiceState.emotion = emotion;

    // Reapply emotional modulation
    if (this.voiceState.isProcessing) {
      this.applyEmotionalModulation();
    }

    this.emit('emotionChanged', { emotion });
  }

  /**
   * Apply voice filter to remote participant
   */
  applyCharacterFilter(spatialSource, character) {
    if (!spatialSource || !this.characterVoiceFilter) return;

    this.characterVoiceFilter.applyFilter(spatialSource, character);
  }

  /**
   * Handle voice activity detection
   */
  handleVoiceActivity(event) {
    const { isActive, level } = event;

    this.voiceState.isActive = isActive;
    this.voiceState.level = level;

    // Update noise gate based on voice activity
    if (this.processingChain.noiseGate) {
      this.processingChain.noiseGate.gain.setValueAtTime(
        isActive ? 1.0 : 0.0,
        this.audioContext.currentTime
      );
    }

    this.emit('voiceActivity', { isActive, level });
  }

  /**
   * Handle speech transcription
   */
  handleTranscription(event) {
    const { text, confidence, isFinal } = event;

    this.emit('transcription', { text, confidence, isFinal });

    // Process for voice commands or translation
    this.processTranscription(text);
  }

  /**
   * Process transcription for commands
   */
  processTranscription(text) {
    // Check for voice commands
    if (text.startsWith('/')) {
      const command = text.substring(1).toLowerCase().trim();
      this.processVoiceCommand(command);
    }
  }

  /**
   * Process voice commands
   */
  processVoiceCommand(command) {
    const commandHandlers = {
      'mute': () => this.mute(),
      'unmute': () => this.unmute(),
      'dwarf': () => this.setCharacterVoice('dwarvish'),
      'elf': () => this.setCharacterVoice('elvish'),
      'orc': () => this.setCharacterVoice('orcish'),
      'human': () => this.setCharacterVoice('human'),
      'dragon': () => this.setCharacterVoice('draconic')
    };

    const handler = commandHandlers[command];
    if (handler) {
      handler();
      this.emit('voiceCommandExecuted', { command });
    }
  }

  /**
   * Mute/unmute local audio
   */
  mute() {
    this.voiceState.isMuted = true;
    if (this.processingChain.noiseGate) {
      this.processingChain.noiseGate.gain.value = 0;
    }
    this.emit('muted');
  }

  unmute() {
    this.voiceState.isMuted = false;
    // Voice activity will control the noise gate
    this.emit('unmuted');
  }

  /**
   * Get current voice state
   */
  getVoiceState() {
    return { ...this.voiceState };
  }

  /**
   * Get voice processing metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      voiceState: this.getVoiceState(),
      activeProcessors: Object.values(this.processingChain).filter(node => node !== null).length
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
          console.error(`Error in voice processor event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup and destroy voice processor
   */
  cleanup() {
    // Stop voice activity detection
    if (this.voiceActivityDetector) {
      this.voiceActivityDetector.stop();
    }

    // Stop speech transcription
    if (this.speechTranscriber) {
      this.speechTranscriber.stop();
    }

    // Disconnect all processing nodes
    Object.values(this.processingChain).forEach(node => {
      if (node && node.disconnect) {
        node.disconnect();
      }
    });

    // Cleanup components
    if (this.noiseSuppressor) {
      this.noiseSuppressor.cleanup();
    }
    if (this.characterVoiceFilter) {
      this.characterVoiceFilter.cleanup();
    }

    // Clear references
    this.processingChain = {};
    this.workletProcessors.clear();
    this.eventListeners.clear();

    this.emit('cleanupComplete');
  }
}