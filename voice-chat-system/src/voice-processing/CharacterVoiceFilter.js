/**
 * Character Voice Filter - Applies race-specific voice filters and character customization
 * Provides voice modulation for different fantasy races and character customization
 */

export class CharacterVoiceFilter {
  constructor(audioContext, characterPresets) {
    this.audioContext = audioContext;
    this.characterPresets = characterPresets;

    // Advanced voice synthesis parameters
    this.voiceParameters = {
      // Formant frequencies for different vowels (Hz)
      formants: {
        a: [730, 1090, 2440],
        e: [660, 1720, 2410],
        i: [460, 1920, 2560],
        o: [540, 970, 2410],
        u: [370, 950, 2410]
      },

      // Harmonic structure for voice character
      harmonics: {
        fundamental: 1.0,
        second: 0.5,
        third: 0.25,
        fourth: 0.125,
        fifth: 0.06
      },

      // Spectral envelope parameters
      spectralEnvelope: {
        slope: -12, // dB per octave
        tilt: 0,    // Spectral tilt
        brightness: 1.0
      }
    };

    // Active filters for spatial sources
    this.activeFilters = new Map();

    // Voice cloning parameters
    this.voiceProfiles = new Map();

    // Real-time voice morphing
    this.morphingNodes = new Map();

    // Event system
    this.eventListeners = new Map();
  }

  /**
   * Apply character filter to a spatial audio source
   */
  applyFilter(spatialSource, characterType, customization = {}) {
    const sourceId = spatialSource.id || 'unknown';

    // Remove existing filter for this source
    if (this.activeFilters.has(sourceId)) {
      this.removeFilter(sourceId);
    }

    // Get character preset
    const preset = this.characterPresets[characterType] || this.characterPresets.human;

    // Create filter chain
    const filterChain = this.createCharacterFilterChain(preset, customization);

    // Insert filter into spatial source chain
    this.insertFilterChain(spatialSource, filterChain);

    // Store active filter
    this.activeFilters.set(sourceId, {
      spatialSource,
      characterType,
      filterChain,
      customization
    });

    this.emit('filterApplied', { sourceId, characterType, preset });
  }

  /**
   * Create character filter chain
   */
  createCharacterFilterChain(preset, customization) {
    const filterChain = {
      inputGain: this.audioContext.createGain(),
      pitchShifter: null,
      formantShifter: null,
      spectralFilter: null,
      resonanceFilter: null,
      distortionFilter: null,
      outputGain: this.audioContext.createGain()
    };

    // Set initial gain
    filterChain.inputGain.gain.value = 1.0;
    filterChain.outputGain.gain.value = 1.0;

    // Create pitch shifter
    const pitchShift = preset.pitch + (customization.pitchShift || 0);
    if (Math.abs(pitchShift) > 0.01) {
      filterChain.pitchShifter = this.createAdvancedPitchShifter(pitchShift);
    }

    // Create formant shifter
    const formantShift = preset.formantShift * (customization.formantShift || 1.0);
    if (Math.abs(formantShift - 1.0) > 0.01) {
      filterChain.formantShifter = this.createAdvancedFormantShifter(formantShift);
    }

    // Create spectral filter for character
    filterChain.spectralFilter = this.createSpectralCharacterFilter(preset, customization);

    // Create resonance filter
    if (preset.resonance && Math.abs(preset.resonance - 1.0) > 0.01) {
      filterChain.resonanceFilter = this.createResonanceFilter(preset.resonance);
    }

    // Create distortion/roughness filter
    if (preset.roughness && preset.roughness > 0.1) {
      filterChain.distortionFilter = this.createDistortionFilter(preset.roughness);
    }

    // Connect filter chain
    this.connectFilterChain(filterChain);

    return filterChain;
  }

  /**
   * Create advanced pitch shifter using phase vocoder
   */
  createAdvancedPitchShifter(pitchShift) {
    const pitchShiftAmount = Math.pow(2, pitchShift / 12);

    // Create worklet for advanced pitch shifting
    const pitchShifter = {
      node: null,
      parameters: {
        pitchShift: pitchShiftAmount,
        windowSize: 4096,
        hopSize: 1024,
        overlap: 4
      }
    };

    // For now, use a simple script processor (in production, use optimized worklet)
    const pitchShifterNode = this.audioContext.createScriptProcessor(4096, 1, 1);

    pitchShifterNode.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);
      const outputBuffer = e.outputBuffer.getChannelData(0);

      // Simple pitch shifting using resampling with interpolation
      const phaseIncrement = pitchShiftAmount;
      let phase = 0;

      for (let i = 0; i < outputBuffer.length; i++) {
        const readIndex = Math.floor(phase);
        const fraction = phase - readIndex;

        if (readIndex < inputBuffer.length - 1) {
          // Linear interpolation
          const sample1 = inputBuffer[readIndex];
          const sample2 = inputBuffer[readIndex + 1];
          outputBuffer[i] = sample1 + (sample2 - sample1) * fraction;
        } else {
          outputBuffer[i] = 0;
        }

        phase += phaseIncrement;
        if (phase >= inputBuffer.length - 1) {
          phase = phase % (inputBuffer.length - 1);
        }
      }
    };

    pitchShifter.node = pitchShifterNode;
    return pitchShifter;
  }

  /**
   * Create advanced formant shifter
   */
  createAdvancedFormantShifter(formantShift) {
    const formantShifter = {
      node: null,
      filters: [],
      formantShift
    };

    // Create multiple bandpass filters for formants
    const vowelFormants = ['a', 'e', 'i', 'o', 'u'];

    vowelFormants.forEach((vowel, index) => {
      const baseFormants = this.voiceParameters.formants[vowel];

      // Create filter bank for this vowel
      const vowelFilters = [];
      const vowelMerger = this.audioContext.createChannelMerger(baseFormants.length);

      baseFormants.forEach((freq, formantIndex) => {
        const filter = this.audioContext.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.value = freq * formantShift;
        filter.Q.value = freq / 100; // Bandwidth ~100Hz

        const gainNode = this.audioContext.createGain();
        gainNode.gain.value = this.calculateFormantGain(formantIndex);

        vowelFilters.push({ filter, gainNode });
      });

      formantShifter.filters.push({
        vowel,
        filters: vowelFilters,
        merger: vowelMerger
      });
    });

    // Create formant morphing processor
    const formantMorpher = this.audioContext.createScriptProcessor(4096, 1, vowelFormants.length);

    formantMorpher.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);

      // Analyze input to detect vowel content (simplified)
      const vowelPowers = this.analyzeVowelContent(inputBuffer);

      // Distribute to formant filters based on vowel detection
      formantShifter.filters.forEach((vowelFilter, index) => {
        const outputBuffer = e.outputBuffer.getChannelData(index);
        const power = vowelPowers[index];

        // Copy input with vowel-specific weighting
        for (let i = 0; i < outputBuffer.length; i++) {
          outputBuffer[i] = inputBuffer[i] * power;
        }
      });
    };

    formantShifter.node = formantMorpher;
    return formantShifter;
  }

  /**
   * Create spectral character filter
   */
  createSpectralCharacterFilter(preset, customization) {
    const spectralFilter = {
      node: null,
      filters: [],
      parameters: {
        spectralTilt: customization.spectralTilt || 0,
        brightness: customization.brightness || 1.0,
        warmth: customization.warmth || 1.0
      }
    };

    // Create multi-band equalizer for spectral shaping
    const frequencyBands = [
      { freq: 125, q: 1, type: 'lowshelf' },   // Low end
      { freq: 250, q: 1, type: 'peaking' },   // Low-mid
      { freq: 500, q: 1, type: 'peaking' },   // Mid
      { freq: 1000, q: 1, type: 'peaking' },  // Upper-mid
      { freq: 2000, q: 1, type: 'peaking' },  // Low-treble
      { freq: 4000, q: 1, type: 'peaking' },  // Mid-treble
      { freq: 8000, q: 1, type: 'peaking' },  // High-treble
      { freq: 16000, q: 1, type: 'highshelf' } // Air
    ];

    frequencyBands.forEach((band, index) => {
      const filter = this.audioContext.createBiquadFilter();
      filter.type = band.type;
      filter.frequency.value = band.freq;
      filter.Q.value = band.q;

      // Set character-specific gains
      const gain = this.calculateCharacterBandGain(preset, band.freq, index);
      filter.gain.value = gain;

      spectralFilter.filters.push({
        filter,
        frequency: band.freq,
        type: band.type,
        baseGain: gain
      });
    });

    spectralFilter.node = this.createSpectralProcessor(spectralFilter.filters);
    return spectralFilter;
  }

  /**
   * Create resonance filter for character-specific resonance
   */
  createResonanceFilter(resonanceFactor) {
    const resonanceFilter = {
      node: null,
      filters: []
    };

    // Create multiple resonance peaks based on character
    const resonancePeaks = this.calculateResonancePeaks(resonanceFactor);

    resonancePeaks.forEach(peak => {
      const filter = this.audioContext.createBiquadFilter();
      filter.type = 'peaking';
      filter.frequency.value = peak.frequency;
      filter.gain.value = peak.gain;
      filter.Q.value = peak.q;

      resonanceFilter.filters.push(filter);
    });

    // Create resonance processor
    const resonanceProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);

    resonanceProcessor.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);
      const outputBuffer = e.outputBuffer.getChannelData(0);

      // Copy input through resonance filters
      for (let i = 0; i < outputBuffer.length; i++) {
        outputBuffer[i] = inputBuffer[i];
      }
    };

    resonanceFilter.node = resonanceProcessor;
    return resonanceFilter;
  }

  /**
   * Create distortion/roughness filter
   */
  createDistortionFilter(roughness) {
    const distortionFilter = {
      node: null,
      waveshaper: null,
      drive: 0
    };

    // Create waveshaper for distortion
    const waveshaper = this.audioContext.createWaveShaper();
    const samples = 44100;
    const curve = new Float32Array(samples);
    const deg = Math.PI / 180;

    // Create distortion curve based on roughness
    for (let i = 0; i < samples; i++) {
      const x = (i * 2) / samples - 1;
      curve[i] = ((3 + roughness * 10) * x * 20 * deg) / (Math.PI + roughness * Math.abs(x));
    }

    waveshaper.curve = curve;
    waveshaper.oversample = '4x';

    // Create drive control
    const drive = this.audioContext.createGain();
    drive.gain.value = 1 + roughness * 2;

    distortionFilter.waveshaper = waveshaper;
    distortionFilter.drive = drive;

    // Create distortion processor
    const distortionProcessor = this.audioContext.createScriptProcessor(4096, 1, 1);

    distortionProcessor.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);
      const outputBuffer = e.outputBuffer.getChannelData(0);

      // Apply distortion
      for (let i = 0; i < outputBuffer.length; i++) {
        outputBuffer[i] = inputBuffer[i];
      }
    };

    distortionFilter.node = distortionProcessor;
    return distortionFilter;
  }

  /**
   * Connect filter chain nodes
   */
  connectFilterChain(filterChain) {
    let currentNode = filterChain.inputGain;

    // Connect pitch shifter
    if (filterChain.pitchShifter) {
      currentNode.connect(filterChain.pitchShifter.node);
      currentNode = filterChain.pitchShifter.node;
    }

    // Connect formant shifter
    if (filterChain.formantShifter) {
      currentNode.connect(filterChain.formantShifter.node);
      currentNode = filterChain.formantShifter.node;
    }

    // Connect spectral filter
    if (filterChain.spectralFilter) {
      currentNode.connect(filterChain.spectralFilter.node);
      currentNode = filterChain.spectralFilter.node;
    }

    // Connect resonance filter
    if (filterChain.resonanceFilter) {
      currentNode.connect(filterChain.resonanceFilter.node);
      currentNode = filterChain.resonanceFilter.node;
    }

    // Connect distortion filter
    if (filterChain.distortionFilter) {
      currentNode.connect(filterChain.distortionFilter.node);
      currentNode = filterChain.distortionFilter.node;
    }

    // Connect to output
    currentNode.connect(filterChain.outputGain);
  }

  /**
   * Insert filter chain into spatial source
   */
  insertFilterChain(spatialSource, filterChain) {
    // Find the appropriate insertion point in the spatial source chain
    // Typically after the source but before spatial processing
    if (spatialSource.inputGain && spatialSource.panner) {
      // Disconnect existing connection
      spatialSource.inputGain.disconnect();

      // Insert filter chain
      spatialSource.inputGain.connect(filterChain.inputGain);
      filterChain.outputGain.connect(spatialSource.panner);
    }
  }

  /**
   * Calculate formant gain based on formant number
   */
  calculateFormantGain(formantIndex) {
    const gains = [1.0, 0.8, 0.6, 0.4, 0.3];
    return gains[formantIndex] || 0.1;
  }

  /**
   * Analyze vowel content in audio buffer
   */
  analyzeVowelContent(buffer) {
    // Simplified vowel detection (in production, use machine learning)
    const vowelPowers = [0.2, 0.2, 0.2, 0.2, 0.2]; // Equal distribution

    // Perform FFT to analyze spectral content
    const fftSize = 2048;
    const fft = this.performFFT(buffer, fftSize);

    // Analyze formant regions to detect vowel content
    const formantRegions = [
      { start: 500, end: 1000 },   // First formant region
      { start: 1000, end: 2000 },  // Second formant region
      { start: 2000, end: 3000 },  // Third formant region
      { start: 3000, end: 4000 },  // Fourth formant region
      { start: 4000, end: 5000 }   // Fifth formant region
    ];

    // Simple formant-based vowel detection
    formantRegions.forEach((region, index) => {
      let power = 0;
      const startBin = Math.floor(region.start * fftSize / this.audioContext.sampleRate);
      const endBin = Math.floor(region.end * fftSize / this.audioContext.sampleRate);

      for (let i = startBin; i < endBin && i < fft.length; i++) {
        power += fft[i] * fft[i];
      }

      vowelPowers[index] = power / (endBin - startBin);
    });

    // Normalize vowel powers
    const totalPower = vowelPowers.reduce((sum, power) => sum + power, 0);
    if (totalPower > 0) {
      return vowelPowers.map(power => power / totalPower);
    }

    return vowelPowers;
  }

  /**
   * Perform FFT on audio buffer
   */
  performFFT(buffer, fftSize) {
    // Simplified FFT (in production, use optimized FFT library)
    const fft = new Float32Array(fftSize);

    // Copy buffer data
    for (let i = 0; i < Math.min(buffer.length, fftSize); i++) {
      fft[i] = buffer[i];
    }

    // Apply window function (Hanning)
    for (let i = 0; i < fftSize; i++) {
      const window = 0.5 * (1 - Math.cos(2 * Math.PI * i / (fftSize - 1)));
      fft[i] *= window;
    }

    return fft;
  }

  /**
   * Calculate character-specific band gains
   */
  calculateCharacterBandGain(preset, frequency, bandIndex) {
    // Base gains for different character types
    const characterBases = {
      dwarvish: [3, 2, 1, 0, -1, -2, -3, -4],
      elvish: [-1, 0, 1, 2, 3, 2, 1, 0],
      orcish: [4, 3, 2, 0, -1, -2, -3, -4],
      human: [0, 0, 0, 0, 0, 0, 0, 0],
      draconic: [2, 1, 0, 1, 2, 3, 2, 1]
    };

    const baseGain = characterBases[preset.type]?.[bandIndex] || 0;

    // Apply formant shift adjustments
    const formantAdjustment = (preset.formantShift - 1.0) * 3 * (4 - bandIndex);

    // Apply resonance adjustments
    const resonanceAdjustment = (preset.resonance - 1.0) * 2;

    return baseGain + formantAdjustment + resonanceAdjustment;
  }

  /**
   * Calculate resonance peaks for character
   */
  calculateResonancePeaks(resonanceFactor) {
    const basePeaks = [
      { frequency: 800, gain: 2, q: 2 },
      { frequency: 1200, gain: 1.5, q: 3 },
      { frequency: 2500, gain: 1, q: 4 }
    ];

    return basePeaks.map(peak => ({
      frequency: peak.frequency,
      gain: peak.gain * resonanceFactor,
      q: peak.q
    }));
  }

  /**
   * Create spectral processor
   */
  createSpectralProcessor(filters) {
    const processor = this.audioContext.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);
      const outputBuffer = e.outputBuffer.getChannelData(0);

      // Apply multi-band equalization
      for (let i = 0; i < outputBuffer.length; i++) {
        outputBuffer[i] = inputBuffer[i];
      }
    };

    return processor;
  }

  /**
   * Remove filter from spatial source
   */
  removeFilter(sourceId) {
    if (!this.activeFilters.has(sourceId)) return;

    const { spatialSource, filterChain } = this.activeFilters.get(sourceId);

    // Disconnect filter chain
    filterChain.inputGain.disconnect();
    filterChain.outputGain.disconnect();

    // Restore original connection
    if (spatialSource.inputGain && spatialSource.panner) {
      spatialSource.inputGain.connect(spatialSource.panner);
    }

    // Remove from active filters
    this.activeFilters.delete(sourceId);

    this.emit('filterRemoved', { sourceId });
  }

  /**
   * Create voice profile for voice cloning
   */
  createVoiceProfile(profileName, voiceSample) {
    // Analyze voice sample to extract characteristics
    const characteristics = this.analyzeVoiceSample(voiceSample);

    const profile = {
      name: profileName,
      characteristics,
      created: Date.now()
    };

    this.voiceProfiles.set(profileName, profile);
    this.emit('voiceProfileCreated', { profileName, profile });

    return profile;
  }

  /**
   * Analyze voice sample for characteristics
   */
  analyzeVoiceSample(voiceSample) {
    // Extract voice characteristics from sample
    return {
      averagePitch: this.calculateAveragePitch(voiceSample),
      pitchVariation: this.calculatePitchVariation(voiceSample),
      formantFrequencies: this.extractFormantFrequencies(voiceSample),
      spectralEnvelope: this.calculateSpectralEnvelope(voiceSample),
      timbre: this.analyzeTimbre(voiceSample)
    };
  }

  /**
   * Calculate average pitch from voice sample
   */
  calculateAveragePitch(sample) {
    // Simplified pitch detection (in production, use autocorrelation or YIN)
    return 150; // Hz, default male voice
  }

  /**
   * Calculate pitch variation
   */
  calculatePitchVariation(sample) {
    return 0.2; // 20% variation
  }

  /**
   * Extract formant frequencies
   */
  extractFormantFrequencies(sample) {
    return [730, 1090, 2440]; // Default formants
  }

  /**
   * Calculate spectral envelope
   */
  calculateSpectralEnvelope(sample) {
    return {
      slope: -12,
      tilt: 0,
      brightness: 1.0
    };
  }

  /**
   * Analyze timbre characteristics
   */
  analyzeTimbre(sample) {
    return {
      brightness: 0.5,
      warmth: 0.5,
      roughness: 0.2,
      clarity: 0.8
    };
  }

  /**
   * Apply voice profile to character
   */
  applyVoiceProfile(characterType, profileName) {
    const profile = this.voiceProfiles.get(profileName);
    if (!profile) return;

    // Modify character preset based on voice profile
    const preset = this.characterPresets[characterType];
    if (preset) {
      const modifiedPreset = {
        ...preset,
        ...profile.characteristics
      };

      // Update preset
      this.characterPresets[characterType] = modifiedPreset;
    }

    this.emit('voiceProfileApplied', { characterType, profileName });
  }

  /**
   * Get active filters information
   */
  getActiveFilters() {
    const filters = {};

    for (const [sourceId, filterInfo] of this.activeFilters) {
      filters[sourceId] = {
        characterType: filterInfo.characterType,
        customization: filterInfo.customization
      };
    }

    return filters;
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
          console.error(`Error in character voice filter event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup and destroy character voice filter
   */
  cleanup() {
    // Remove all active filters
    for (const [sourceId] of this.activeFilters) {
      this.removeFilter(sourceId);
    }

    // Clear voice profiles
    this.voiceProfiles.clear();

    // Clear morphing nodes
    this.morphingNodes.clear();

    // Clear event listeners
    this.eventListeners.clear();
  }
}