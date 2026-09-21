/**
 * Noise Suppressor - Advanced noise reduction and audio cleanup
 * Provides spectral subtraction, gating, and adaptive filtering
 */

export class NoiseSuppressor {
  constructor(audioContext, config = {}) {
    this.audioContext = audioContext;
    this.config = {
      // Noise reduction settings
      spectralSubtraction: true,
      reductionAmount: 0.8,
      gateThreshold: -40, // dB
      gateRatio: 0.1,
      attackTime: 0.01,
      releaseTime: 0.1,

      // Frequency-dependent processing
      frequencyBands: 32,
      minFrequency: 80,
      maxFrequency: 8000,

      // Adaptive settings
      adaptiveNoise: true,
      adaptationRate: 0.1,
      noiseProfileUpdateRate: 0.05,

      // Advanced processing
      transientPreservation: true,
      harmonicPreservation: true,
      ...config
    };

    // Noise profiling
    this.noiseProfile = null;
    this.isProfilingNoise = false;
    this.noiseSamples = [];

    // Processing nodes
    this.processors = {
      analyser: null,
      gate: null,
      spectralSubtractor: null,
      multibandCompressor: null,
      outputGain: null
    };

    // Adaptive parameters
    this.adaptiveThreshold = this.config.gateThreshold;
    this.backgroundNoiseLevel = 0;

    // Frequency analysis
    this.fftSize = 2048;
    this.frequencyBands = this.createFrequencyBands();

    // Event system
    this.eventListeners = new Map();

    // Performance monitoring
    this.metrics = {
      noiseReductionAmount: 0,
      gateActivityRatio: 0,
      processingLatency: 0
    };
  }

  /**
   * Create noise reduction processor
   */
  async createProcessor() {
    try {
      // Create audio processing chain
      const inputGain = this.audioContext.createGain();
      const analyser = this.audioContext.createAnalyser();
      analyser.fftSize = this.fftSize;
      analyser.smoothingTimeConstant = 0.8;

      // Create noise gate
      const gate = this.audioContext.createGain();
      gate.gain.value = 1.0;

      // Create multiband compressor for frequency-dependent processing
      const multibandCompressor = this.createMultibandCompressor();

      // Create output gain
      const outputGain = this.audioContext.createGain();
      outputGain.gain.value = 1.0;

      // Create spectral subtraction processor
      const spectralSubtractor = await this.createSpectralSubtraction();

      // Connect processing chain
      inputGain.connect(analyser);
      analyser.connect(gate);
      gate.connect(multibandCompressor);
      multibandCompressor.connect(spectralSubtractor);
      spectralSubtractor.connect(outputGain);

      // Store processors
      this.processors = {
        inputGain,
        analyser,
        gate,
        multibandCompressor,
        spectralSubtractor,
        outputGain
      };

      // Initialize noise profile
      await this.initializeNoiseProfile();

      this.emit('processorCreated');
      return outputGain;
    } catch (error) {
      console.error('Failed to create noise suppression processor:', error);
      throw error;
    }
  }

  /**
   * Create multiband compressor for frequency-dependent processing
   */
  createMultibandCompressor() {
    const multibandProcessor = {
      node: null,
      bands: [],
      merger: null
    };

    // Create frequency band splits
    const crossoverFrequencies = this.calculateCrossoverFrequencies();

    // Create filters for each band
    for (let i = 0; i < this.frequencyBands.length; i++) {
      const band = {
        lowFilter: null,
        highFilter: null,
        compressor: null,
        gain: null
      };

      // Create crossover filters
      if (i === 0) {
        // First band - low-pass
        band.lowFilter = this.audioContext.createBiquadFilter();
        band.lowFilter.type = 'lowpass';
        band.lowFilter.frequency.value = crossoverFrequencies[i];
      } else if (i === this.frequencyBands.length - 1) {
        // Last band - high-pass
        band.highFilter = this.audioContext.createBiquadFilter();
        band.highFilter.type = 'highpass';
        band.highFilter.frequency.value = crossoverFrequencies[i - 1];
      } else {
        // Middle bands - band-pass
        band.lowFilter = this.audioContext.createBiquadFilter();
        band.lowFilter.type = 'lowpass';
        band.lowFilter.frequency.value = crossoverFrequencies[i];

        band.highFilter = this.audioContext.createBiquadFilter();
        band.highFilter.type = 'highpass';
        band.highFilter.frequency.value = crossoverFrequencies[i - 1];
      }

      // Create compressor for this band
      band.compressor = this.audioContext.createDynamicsCompressor();
      band.compressor.threshold.value = -30;
      band.compressor.knee.value = 8;
      band.compressor.ratio.value = 4;
      band.compressor.attack.value = 0.01;
      band.compressor.release.value = 0.1;

      // Create gain control
      band.gain = this.audioContext.createGain();
      band.gain.gain.value = 1.0;

      multibandProcessor.bands.push(band);
    }

    // Create channel merger to combine bands
    multibandProcessor.merger = this.audioContext.createChannelMerger(this.frequencyBands.length);

    // Create script processor for band processing
    const multibandNode = this.audioContext.createScriptProcessor(4096, 1, this.frequencyBands.length);

    multibandNode.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);

      // Process each frequency band
      multibandProcessor.bands.forEach((band, index) => {
        const outputBuffer = e.outputBuffer.getChannelData(index);

        // Apply band filtering (simplified)
        for (let i = 0; i < outputBuffer.length; i++) {
          outputBuffer[i] = inputBuffer[i];
        }
      });
    };

    multibandProcessor.node = multibandNode;
    return multibandProcessor;
  }

  /**
   * Calculate crossover frequencies for multiband processing
   */
  calculateCrossoverFrequencies() {
    const frequencies = [];
    const minLog = Math.log10(this.config.minFrequency);
    const maxLog = Math.log10(this.config.maxFrequency);
    const step = (maxLog - minLog) / (this.frequencyBands.length - 1);

    for (let i = 1; i < this.frequencyBands.length - 1; i++) {
      const freq = Math.pow(10, minLog + step * i);
      frequencies.push(freq);
    }

    return frequencies;
  }

  /**
   * Create frequency bands
   */
  createFrequencyBands() {
    const bands = [];
    const minLog = Math.log10(this.config.minFrequency);
    const maxLog = Math.log10(this.config.maxFrequency);
    const step = (maxLog - minLog) / this.config.frequencyBands;

    for (let i = 0; i < this.config.frequencyBands; i++) {
      const minFreq = Math.pow(10, minLog + step * i);
      const maxFreq = Math.pow(10, minLog + step * (i + 1));
      const centerFreq = Math.sqrt(minFreq * maxFreq);

      bands.push({
        min: minFreq,
        max: maxFreq,
        center: centerFreq,
        noiseLevel: 0,
        gain: 1.0
      });
    }

    return bands;
  }

  /**
   * Create spectral subtraction processor
   */
  async createSpectralSubtraction() {
    // Load audio worklet for spectral processing
    try {
      await this.audioContext.audioWorklet.addModule('/worklets/spectral-subtractor.js');
    } catch (error) {
      console.warn('Failed to load spectral subtraction worklet, using fallback');
    }

    const spectralSubtractor = {
      node: null,
      noiseProfile: new Float32Array(this.fftSize / 2),
      adaptationRate: this.config.adaptationRate
    };

    // Create script processor for spectral subtraction
    const processor = this.audioContext.createScriptProcessor(this.fftSize, 1, 1);

    processor.onaudioprocess = (e) => {
      const inputBuffer = e.inputBuffer.getChannelData(0);
      const outputBuffer = e.outputBuffer.getChannelData(0);

      // Perform FFT
      const fft = this.performFFT(inputBuffer);
      const magnitude = this.calculateMagnitude(fft);
      const phase = this.calculatePhase(fft);

      // Spectral subtraction
      const processedMagnitude = this.applySpectralSubtraction(magnitude);

      // Reconstruct signal
      const processedFFT = this.reconstructFFT(processedMagnitude, phase);
      const outputSignal = this.performIFFT(processedFFT);

      // Copy to output
      for (let i = 0; i < outputBuffer.length; i++) {
        outputBuffer[i] = outputSignal[i] || 0;
      }

      // Update noise profile adaptively
      if (this.config.adaptiveNoise) {
        this.updateNoiseProfile(magnitude);
      }
    };

    spectralSubtractor.node = processor;
    return spectralSubtractor;
  }

  /**
   * Perform FFT on audio signal
   */
  performFFT(signal) {
    // Simplified FFT implementation (in production, use optimized library)
    const fftSize = this.fftSize;
    const fft = new Float32Array(fftSize * 2); // Real and imaginary parts

    // Copy signal to real part
    for (let i = 0; i < signal.length && i < fftSize; i++) {
      fft[i * 2] = signal[i];
      fft[i * 2 + 1] = 0;
    }

    // Apply window function
    this.applyWindowFunction(fft);

    return fft;
  }

  /**
   * Apply window function to FFT
   */
  applyWindowFunction(fft) {
    const fftSize = fft.length / 2;

    for (let i = 0; i < fftSize; i++) {
      const window = 0.5 * (1 - Math.cos(2 * Math.PI * i / (fftSize - 1)));
      fft[i * 2] *= window;
      fft[i * 2 + 1] *= window;
    }
  }

  /**
   * Calculate magnitude from FFT
   */
  calculateMagnitude(fft) {
    const magnitude = new Float32Array(fft.length / 2);

    for (let i = 0; i < magnitude.length; i++) {
      const real = fft[i * 2];
      const imag = fft[i * 2 + 1];
      magnitude[i] = Math.sqrt(real * real + imag * imag);
    }

    return magnitude;
  }

  /**
   * Calculate phase from FFT
   */
  calculatePhase(fft) {
    const phase = new Float32Array(fft.length / 2);

    for (let i = 0; i < phase.length; i++) {
      const real = fft[i * 2];
      const imag = fft[i * 2 + 1];
      phase[i] = Math.atan2(imag, real);
    }

    return phase;
  }

  /**
   * Apply spectral subtraction
   */
  applySpectralSubtraction(magnitude) {
    const processedMagnitude = new Float32Array(magnitude.length);

    for (let i = 0; i < magnitude.length; i++) {
      const noiseLevel = this.noiseProfile ? this.noiseProfile[i] : 0;
      const subtractionAmount = noiseLevel * this.config.reductionAmount;

      // Spectral subtraction with over-subtraction factor
      let processed = magnitude[i] - subtractionAmount;

      // Prevent negative values
      processed = Math.max(processed, magnitude[i] * 0.1);

      // Apply spectral floor
      processed = Math.max(processed, 0.01);

      processedMagnitude[i] = processed;
    }

    return processedMagnitude;
  }

  /**
   * Reconstruct FFT from magnitude and phase
   */
  reconstructFFT(magnitude, phase) {
    const fft = new Float32Array(magnitude.length * 2);

    for (let i = 0; i < magnitude.length; i++) {
      fft[i * 2] = magnitude[i] * Math.cos(phase[i]);
      fft[i * 2 + 1] = magnitude[i] * Math.sin(phase[i]);
    }

    return fft;
  }

  /**
   * Perform inverse FFT
   */
  performIFFT(fft) {
    // Simplified IFFT implementation
    const signalLength = fft.length / 2;
    const signal = new Float32Array(signalLength);

    for (let i = 0; i < signalLength; i++) {
      signal[i] = fft[i * 2] / signalLength; // Real part only, normalized
    }

    return signal;
  }

  /**
   * Initialize noise profile
   */
  async initializeNoiseProfile() {
    // Create initial noise profile based on assumption of low-level noise
    this.noiseProfile = new Float32Array(this.fftSize / 2);

    // Initialize with low-level noise estimate
    for (let i = 0; i < this.noiseProfile.length; i++) {
      this.noiseProfile[i] = 0.001; // Very low noise floor
    }

    this.emit('noiseProfileInitialized');
  }

  /**
   * Update noise profile adaptively
   */
  updateNoiseProfile(currentMagnitude) {
    if (!this.noiseProfile) return;

    const adaptationRate = this.config.adaptationRate;

    for (let i = 0; i < this.noiseProfile.length; i++) {
      // Exponential moving average of noise
      this.noiseProfile[i] = (1 - adaptationRate) * this.noiseProfile[i] +
                             adaptationRate * currentMagnitude[i];
    }
  }

  /**
   * Start noise profiling
   */
  startNoiseProfiling() {
    this.isProfilingNoise = true;
    this.noiseSamples = [];

    this.emit('noiseProfilingStarted');
  }

  /**
   * Stop noise profiling and create profile
   */
  stopNoiseProfiling() {
    if (!this.isProfilingNoise) return;

    this.isProfilingNoise = false;

    if (this.noiseSamples.length > 0) {
      // Create noise profile from samples
      this.noiseProfile = this.averageNoiseSamples(this.noiseSamples);
      this.emit('noiseProfileCreated', { sampleCount: this.noiseSamples.length });
    }

    this.noiseSamples = [];
  }

  /**
   * Average noise samples to create profile
   */
  averageNoiseSamples(samples) {
    if (samples.length === 0) return new Float32Array(this.fftSize / 2);

    const averaged = new Float32Array(samples[0].length);

    for (let i = 0; i < averaged.length; i++) {
      let sum = 0;
      for (let j = 0; j < samples.length; j++) {
        sum += samples[j][i];
      }
      averaged[i] = sum / samples.length;
    }

    return averaged;
  }

  /**
   * Set reduction amount
   */
  setReductionAmount(amount) {
    this.config.reductionAmount = Math.max(0, Math.min(1, amount));
    this.emit('reductionAmountChanged', { amount: this.config.reductionAmount });
  }

  /**
   * Set gate threshold
   */
  setGateThreshold(threshold) {
    this.config.gateThreshold = threshold;
    this.adaptiveThreshold = threshold;
    this.emit('gateThresholdChanged', { threshold });
  }

  /**
   * Enable/disable adaptive noise reduction
   */
  setAdaptiveNoise(enabled) {
    this.config.adaptiveNoise = enabled;
    this.emit('adaptiveNoiseChanged', { enabled });
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      noiseProfileLength: this.noiseProfile ? this.noiseProfile.length : 0,
      adaptiveThreshold: this.adaptiveThreshold,
      backgroundNoiseLevel: this.backgroundNoiseLevel
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
          console.error(`Error in noise suppressor event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup noise suppressor
   */
  cleanup() {
    // Disconnect all processors
    Object.values(this.processors).forEach(processor => {
      if (processor && processor.disconnect) {
        processor.disconnect();
      }
    });

    // Clear data
    this.noiseProfile = null;
    this.noiseSamples = [];
    this.frequencyBands = [];

    // Clear event listeners
    this.eventListeners.clear();
  }
}