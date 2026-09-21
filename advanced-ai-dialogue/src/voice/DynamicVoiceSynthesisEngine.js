const EventEmitter = require('events');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

class DynamicVoiceSynthesisEngine extends EventEmitter {
  constructor(options = {}) {
    super();

    // Voice synthesis providers
    this.providers = {
      elevenlabs: null,
      google: null,
      azure: null,
      aws: null,
      local: null
    };

    // Voice profiles for different character types
    this.voiceProfiles = new Map();
    this.initializeVoiceProfiles();

    // Emotional tone modifiers
    this.emotionalTones = {
      neutral: { pitch: 1.0, speed: 1.0, volume: 0.8, emphasis: 0.3 },
      happy: { pitch: 1.2, speed: 1.1, volume: 0.9, emphasis: 0.6 },
      sad: { pitch: 0.8, speed: 0.9, volume: 0.7, emphasis: 0.2 },
      angry: { pitch: 1.3, speed: 1.2, volume: 1.0, emphasis: 0.8 },
      fearful: { pitch: 1.1, speed: 0.8, volume: 0.6, emphasis: 0.4 },
      surprised: { pitch: 1.4, speed: 1.3, volume: 0.9, emphasis: 0.7 },
      disgusted: { pitch: 0.9, speed: 0.9, volume: 0.7, emphasis: 0.3 },
      excited: { pitch: 1.3, speed: 1.2, volume: 0.95, emphasis: 0.8 },
      calm: { pitch: 0.9, speed: 0.8, volume: 0.75, emphasis: 0.2 },
      mysterious: { pitch: 0.85, speed: 0.7, volume: 0.6, emphasis: 0.4 }
    };

    // Accent and dialect patterns
    this.accentPatterns = new Map();
    this.initializeAccentPatterns();

    // Age-based voice characteristics
    this.ageCharacteristics = {
      young: { pitch: 1.3, tone: 'bright', clarity: 0.9, energy: 0.9 },
      adult: { pitch: 1.0, tone: 'balanced', clarity: 0.95, energy: 0.8 },
      middle: { pitch: 0.9, tone: 'warm', clarity: 0.9, energy: 0.7 },
      old: { pitch: 0.8, tone: 'raspy', clarity: 0.8, energy: 0.6 }
    };

    // Configuration
    this.options = {
      defaultProvider: options.defaultProvider || 'elevenlabs',
      cacheDirectory: options.cacheDirectory || './voice-cache',
      maxCacheSize: options.maxCacheSize || 1000,
      quality: options.quality || 'high',
      enableEmotionalModulation: options.enableEmotionalModulation !== false,
      enableRealTimeProcessing: options.enableRealTimeProcessing || false,
      maxRealTimeLatency: options.maxRealTimeLatency || 500,
      ...options
    };

    // Cache for generated audio
    this.audioCache = new Map();
    this.cacheCleanupInterval = null;

    // Initialize providers
    this.initializeProviders();

    // Start cache cleanup
    this.startCacheCleanup();

    // Processing queue for real-time synthesis
    this.processingQueue = [];
    this.isProcessing = false;
  }

  initializeVoiceProfiles() {
    // D&D character voice profiles
    this.voiceProfiles.set('dwarf_male', {
      baseVoice: 'deep_gravelly',
      pitch: 0.8,
      speed: 0.85,
      tone: 'rumbling',
      accent: 'nordic',
      characteristics: ['gravelly', 'resonant', 'deliberate']
    });

    this.voiceProfiles.set('dwarf_female', {
      baseVoice: 'mezzo_contralto',
      pitch: 0.85,
      speed: 0.9,
      tone: 'warm_resonant',
      accent: 'nordic',
      characteristics: ['warm', 'strong', 'grounded']
    });

    this.voiceProfiles.set('elf_male', {
      baseVoice: 'lyrical_baritone',
      pitch: 1.1,
      speed: 0.9,
      tone: 'melodic',
      accent: 'elvish',
      characteristics: ['melodic', 'precise', 'ethereal']
    });

    this.voiceProfiles.set('elf_female', {
      baseVoice: 'soprano_clear',
      pitch: 1.2,
      speed: 0.85,
      tone: 'crystalline',
      accent: 'elvish',
      characteristics: ['crystalline', 'graceful', 'flowing']
    });

    this.voiceProfiles.set('human_male_noble', {
      baseVoice: 'baritone_commanding',
      pitch: 1.0,
      speed: 0.95,
      tone: 'authoritative',
      accent: 'standard',
      characteristics: ['authoritative', 'clear', 'confident']
    });

    this.voiceProfiles.set('human_female_noble', {
      baseVoice: 'mezzo_soprano',
      pitch: 1.05,
      speed: 0.9,
      tone: 'refined',
      accent: 'standard',
      characteristics: ['refined', 'elegant', 'poised']
    });

    this.voiceProfiles.set('human_male_common', {
      baseVoice: 'baritone_raspy',
      pitch: 0.95,
      speed: 1.0,
      tone: 'earthy',
      accent: 'common',
      characteristics: ['earthy', 'practical', 'direct']
    });

    this.voiceProfiles.set('human_female_common', {
      baseVoice: 'soprano_bright',
      pitch: 1.1,
      speed: 1.05,
      tone: 'cheerful',
      accent: 'common',
      characteristics: ['cheerful', 'approachable', 'energetic']
    });

    this.voiceProfiles.set('orc_male', {
      baseVoice: 'bass_gruff',
      pitch: 0.7,
      speed: 0.8,
      tone: 'guttural',
      accent: 'orcish',
      characteristics: ['guttural', 'forceful', 'aggressive']
    });

    this.voiceProfiles.set('dragon_ancient', {
      baseVoice: 'bass_resonant',
      pitch: 0.5,
      speed: 0.6,
      tone: 'rumbling',
      accent: 'draconic',
      characteristics: ['rumbling', 'ancient', 'powerful', 'reverberating']
    });
  }

  initializeAccentPatterns() {
    // Accent patterns for different cultures
    this.accentPatterns.set('nordic', {
      vowelShifts: { 'a': 'ah', 'o': 'oh', 'i': 'ee' },
      consonantModifications: { 'th': 't', 'w': 'v' },
      rhythm: 'deliberate',
      melody: 'descending',
      commonPhrases: ['By Odin\'s beard!', 'Hark!', 'Indeed']
    });

    this.accentPatterns.set('elvish', {
      vowelShifts: { 'a': 'ah', 'e': 'ay', 'i': 'ee', 'o': 'oh', 'u': 'oo' },
      consonantModifications: { 'th': 's', 'r': 'rr' },
      rhythm: 'flowing',
      melody: 'ascending',
      commonPhrases: ['As the stars guide...', 'Indeed...', 'Naturally...']
    });

    this.accentPatterns.set('orcish', {
      vowelShifts: { 'a': 'ah', 'o': 'aw', 'u': 'uh' },
      consonantModifications: { 'th': 'd', 's': 'z' },
      rhythm: 'staccato',
      melody: 'aggressive',
      commonPhrases: ['GRAH!', 'You will!', 'Strength!']
    });

    this.accentPatterns.set('draconic', {
      vowelShifts: { 'a': 'ah', 'e': 'eh', 'i': 'ih', 'o': 'oh', 'u': 'uh' },
      consonantModifications: { 'th': 'th', 's': 'ss', 'r': 'rrr' },
      rhythm: 'majestic',
      melody: 'resonant',
      commonPhrases: ['Mortal...', 'Indeed...', 'Remember...']
    });
  }

  initializeProviders() {
    // Initialize ElevenLabs provider
    try {
      const ElevenLabs = require('elevenlabs');
      this.providers.elevenlabs = new ElevenLabs({
        apiKey: process.env.ELEVENLABS_API_KEY
      });
    } catch (error) {
      console.warn('ElevenLabs provider not available:', error.message);
    }

    // Initialize Google Cloud Text-to-Speech
    try {
      const textToSpeech = require('@google-cloud/text-to-speech');
      this.providers.google = new textToSpeech.TextToSpeechClient();
    } catch (error) {
      console.warn('Google TTS provider not available:', error.message);
    }

    // Initialize local TTS (festival/espeak)
    this.providers.local = {
      available: this.checkLocalTTS(),
      engine: this.detectLocalTTSEngine()
    };
  }

  checkLocalTTS() {
    try {
      require('child_process').execSync('which festival || which espeak || which say');
      return true;
    } catch (error) {
      return false;
    }
  }

  detectLocalTTSEngine() {
    try {
      require('child_process').execSync('which festival');
      return 'festival';
    } catch (error) {
      try {
        require('child_process').execSync('which espeak');
        return 'espeak';
      } catch (error) {
        try {
          require('child_process').execSync('which say');
          return 'say';
        } catch (error) {
          return null;
        }
      }
    }
  }

  async synthesizeSpeech(text, voiceConfig, emotionalState = {}, options = {}) {
    try {
      // Generate cache key
      const cacheKey = this.generateCacheKey(text, voiceConfig, emotionalState, options);

      // Check cache first
      if (this.audioCache.has(cacheKey)) {
        const cachedAudio = this.audioCache.get(cacheKey);
        this.emit('speechSynthesized', {
          text,
          voiceConfig,
          emotionalState,
          audioBuffer: cachedAudio,
          cached: true,
          timestamp: new Date().toISOString()
        });
        return cachedAudio;
      }

      // Process text with emotional and accent modifications
      const processedText = this.processTextWithModifiers(text, voiceConfig, emotionalState);

      // Select provider
      const provider = this.selectProvider(options.provider || this.options.defaultProvider);

      // Synthesize speech
      const audioBuffer = await this.synthesizeWithProvider(
        processedText,
        voiceConfig,
        emotionalState,
        provider,
        options
      );

      // Apply post-processing
      const processedAudio = await this.postProcessAudio(audioBuffer, emotionalState, voiceConfig);

      // Cache the result
      this.cacheAudio(cacheKey, processedAudio);

      this.emit('speechSynthesized', {
        text,
        voiceConfig,
        emotionalState,
        audioBuffer: processedAudio,
        cached: false,
        provider: provider.name,
        timestamp: new Date().toISOString()
      });

      return processedAudio;

    } catch (error) {
      console.error('Error synthesizing speech:', error);
      this.emit('synthesisError', {
        text,
        voiceConfig,
        emotionalState,
        error: error.message,
        timestamp: new Date().toISOString()
      });
      throw new Error(`Speech synthesis failed: ${error.message}`);
    }
  }

  async synthesizeSpeechRealtime(text, voiceConfig, emotionalState = {}, options = {}) {
    return new Promise((resolve, reject) => {
      const synthesisRequest = {
        id: Date.now().toString(),
        text,
        voiceConfig,
        emotionalState,
        options,
        resolve,
        reject,
        timestamp: Date.now()
      };

      this.processingQueue.push(synthesisRequest);
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.isProcessing || this.processingQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.processingQueue.length > 0) {
      const request = this.processingQueue.shift();
      const startTime = Date.now();

      try {
        const audioBuffer = await this.synthesizeSpeech(
          request.text,
          request.voiceConfig,
          request.emotionalState,
          { ...request.options, realtime: true }
        );

        const processingTime = Date.now() - startTime;
        const latencyMet = processingTime <= this.options.maxRealTimeLatency;

        request.resolve({
          audioBuffer,
          processingTime,
          latencyMet,
          requestId: request.id
        });

      } catch (error) {
        request.reject(error);
      }
    }

    this.isProcessing = false;
  }

  processTextWithModifiers(text, voiceConfig, emotionalState) {
    let processedText = text;

    // Apply accent modifications
    if (voiceConfig.accent && this.accentPatterns.has(voiceConfig.accent)) {
      processedText = this.applyAccentModifications(processedText, voiceConfig.accent);
    }

    // Add emotional markers for providers that support them
    if (this.options.enableEmotionalModulation && Object.keys(emotionalState).length > 0) {
      processedText = this.addEmotionalMarkers(processedText, emotionalState);
    }

    // Add prosody markers
    processedText = this.addProsodyMarkers(processedText, voiceConfig, emotionalState);

    return processedText;
  }

  applyAccentModifications(text, accentType) {
    const pattern = this.accentPatterns.get(accentType);
    if (!pattern) return text;

    let modifiedText = text;

    // Apply vowel shifts
    for (const [from, to] of Object.entries(pattern.vowelShifts)) {
      const regex = new RegExp(from, 'gi');
      modifiedText = modifiedText.replace(regex, to);
    }

    // Apply consonant modifications
    for (const [from, to] of Object.entries(pattern.consonantModifications)) {
      const regex = new RegExp(from, 'gi');
      modifiedText = modifiedText.replace(regex, to);
    }

    return modifiedText;
  }

  addEmotionalMarkers(text, emotionalState) {
    const dominantEmotion = this.getDominantEmotion(emotionalState);
    const intensity = emotionalState[dominantEmotion] || 0.5;

    let markedText = text;

    switch (dominantEmotion) {
      case 'happy':
        markedText = `<happy intensity="${intensity}">${text}</happy>`;
        break;
      case 'sad':
        markedText = `<sad intensity="${intensity}">${text}</sad>`;
        break;
      case 'angry':
        markedText = `<angry intensity="${intensity}">${text}</angry>`;
        break;
      case 'fearful':
        markedText = `<fear intensity="${intensity}">${text}</fear>`;
        break;
      case 'surprised':
        markedText = `<surprised intensity="${intensity}">${text}</surprised>`;
        break;
      case 'excited':
        markedText = `<excited intensity="${intensity}">${text}</excited>`;
        break;
    }

    return markedText;
  }

  addProsodyMarkers(text, voiceConfig, emotionalState) {
    const tone = this.emotionalTones[this.getDominantEmotion(emotionalState)] || this.emotionalTones.neutral;

    let prosodyText = text;

    // Add emphasis for important words
    const importantWords = this.extractImportantWords(text);
    importantWords.forEach(word => {
      const regex = new RegExp(`\\b${word}\\b`, 'gi');
      prosodyText = prosodyText.replace(regex, `<emphasis level="${tone.emphasis}">${word}</emphasis>`);
    });

    // Add pauses for punctuation
    prosodyText = prosodyText.replace(/\./g, '. <break time="500ms"/>');
    prosodyText = prosodyText.replace(/,/g, ', <break time="200ms"/>');
    prosodyText = prosodyText.replace(/\?/g, '? <break time="300ms"/>');
    prosodyText = prosodyText.replace(/!/g, '! <break time="400ms"/>');

    return prosodyText;
  }

  extractImportantWords(text) {
    // Simple important word extraction - can be enhanced with NLP
    const importantWords = ['important', 'critical', 'danger', 'help', 'please', 'thank', 'yes', 'no'];
    const words = text.toLowerCase().split(/\s+/);

    return words.filter(word =>
      importantWords.some(important => word.includes(important)) ||
      word.length > 6 ||
      word === word.toUpperCase()
    );
  }

  getDominantEmotion(emotionalState) {
    return Object.entries(emotionalState).reduce((dominant, [emotion, intensity]) =>
      intensity > emotionalState[dominant] ? emotion : dominant,
      'neutral'
    );
  }

  selectProvider(providerName) {
    const provider = this.providers[providerName];

    if (!provider) {
      console.warn(`Provider ${providerName} not available, falling back to local`);
      return { name: 'local', provider: this.providers.local };
    }

    if (providerName === 'local' && !provider.available) {
      console.warn('Local TTS not available, falling back to first available provider');
      for (const [name, p] of Object.entries(this.providers)) {
        if (name !== 'local' && p) {
          return { name, provider: p };
        }
      }
    }

    return { name: providerName, provider };
  }

  async synthesizeWithProvider(text, voiceConfig, emotionalState, provider, options) {
    switch (provider.name) {
      case 'elevenlabs':
        return await this.synthesizeWithElevenLabs(text, voiceConfig, emotionalState, options);
      case 'google':
        return await this.synthesizeWithGoogle(text, voiceConfig, emotionalState, options);
      case 'local':
        return await this.synthesizeWithLocal(text, voiceConfig, emotionalState, options);
      default:
        throw new Error(`Unsupported provider: ${provider.name}`);
    }
  }

  async synthesizeWithElevenLabs(text, voiceConfig, emotionalState, options) {
    const voiceProfile = this.getVoiceProfile(voiceConfig);
    const emotionalTone = this.emotionalTones[this.getDominantEmotion(emotionalState)] || this.emotionalTones.neutral;

    const synthesisOptions = {
      voice_id: voiceProfile.elevenLabsId || 'rachel',
      text: text,
      model_id: options.modelId || 'eleven_multilingual_v2',
      voice_settings: {
        stability: 0.75,
        similarity_boost: 0.75,
        style: emotionalTone.emphasis > 0.5 ? 0.5 : 0.0,
        use_speaker_boost: true
      },
      pronunciation_dictionary_locators: []
    };

    try {
      const response = await this.providers.elevenlabs.generate(synthesisOptions);
      return response.audio;
    } catch (error) {
      throw new Error(`ElevenLabs synthesis failed: ${error.message}`);
    }
  }

  async synthesizeWithGoogle(text, voiceConfig, emotionalState, options) {
    const voiceProfile = this.getVoiceProfile(voiceConfig);
    const emotionalTone = this.emotionalTones[this.getDominantEmotion(emotionalState)] || this.emotionalTones.neutral;

    const request = {
      input: { text: text },
      voice: {
        languageCode: voiceProfile.language || 'en-US',
        name: voiceProfile.googleVoice || 'en-US-Standard-C',
        ssmlGender: voiceProfile.gender || 'NEUTRAL'
      },
      audioConfig: {
        audioEncoding: 'MP3',
        speakingRate: emotionalTone.speed * (voiceProfile.speed || 1.0),
        pitch: emotionalTone.pitch * (voiceProfile.pitch || 1.0),
        volumeGainDb: (emotionalTone.volume - 0.8) * 10
      }
    };

    try {
      const [response] = await this.providers.google.synthesizeSpeech(request);
      return response.audioContent;
    } catch (error) {
      throw new Error(`Google TTS synthesis failed: ${error.message}`);
    }
  }

  async synthesizeWithLocal(text, voiceConfig, emotionalState, options) {
    const emotionalTone = this.emotionalTones[this.getDominantEmotion(emotionalState)] || this.emotionalTones.neutral;

    return new Promise((resolve, reject) => {
      let command, args;

      switch (this.providers.local.engine) {
        case 'festival':
          command = 'text2wave';
          args = ['-eval', '(voice_rab_diphone)', '-o', '/dev/stdout'];
          break;
        case 'espeak':
          command = 'espeak';
          args = [
            '-s', Math.round(150 * emotionalTone.speed),
            '-p', Math.round(50 * emotionalTone.pitch),
            '-a', Math.round(emotionalTone.volume * 100),
            '-w', '/dev/stdout'
          ];
          break;
        case 'say':
          command = 'say';
          args = [
            '-r', Math.round(150 * emotionalTone.speed),
            '-p', Math.round(50 * emotionalTone.pitch),
            '--data-format=LEF32@16000',
            '-o', '/dev/stdout'
          ];
          break;
        default:
          return reject(new Error('No local TTS engine available'));
      }

      const process = spawn(command, [...args, text]);
      const chunks = [];

      process.stdout.on('data', (chunk) => {
        chunks.push(chunk);
      });

      process.on('close', (code) => {
        if (code === 0) {
          resolve(Buffer.concat(chunks));
        } else {
          reject(new Error(`Local TTS process exited with code ${code}`));
        }
      });

      process.on('error', (error) => {
        reject(new Error(`Local TTS process error: ${error.message}`));
      });
    });
  }

  async postProcessAudio(audioBuffer, emotionalState, voiceConfig) {
    let processedBuffer = audioBuffer;

    // Apply age-based processing
    if (voiceConfig.age) {
      processedBuffer = await this.applyAgeCharacteristics(processedBuffer, voiceConfig.age);
    }

    // Apply environmental effects
    if (voiceConfig.environment) {
      processedBuffer = await this.applyEnvironmentalEffects(processedBuffer, voiceConfig.environment);
    }

    // Apply vocal characteristics
    if (voiceConfig.characteristics) {
      processedBuffer = await this.applyVocalCharacteristics(processedBuffer, voiceConfig.characteristics);
    }

    return processedBuffer;
  }

  async applyAgeCharacteristics(audioBuffer, age) {
    const characteristics = this.ageCharacteristics[age];
    if (!characteristics) return audioBuffer;

    // Apply age-based audio processing
    // This would typically involve audio processing libraries
    // For now, we'll return the original buffer
    return audioBuffer;
  }

  async applyEnvironmentalEffects(audioBuffer, environment) {
    // Apply environmental effects like reverb, echo, etc.
    // This would involve audio processing libraries
    return audioBuffer;
  }

  async applyVocalCharacteristics(audioBuffer, characteristics) {
    // Apply vocal characteristics like gravelly, breathy, etc.
    // This would involve audio processing libraries
    return audioBuffer;
  }

  getVoiceProfile(voiceConfig) {
    const profileKey = `${voiceConfig.race}_${voiceConfig.gender}_${voiceConfig.socialClass || 'common'}`;
    const profile = this.voiceProfiles.get(profileKey);

    if (profile) {
      return { ...profile, ...voiceConfig };
    }

    // Fallback to generic profile
    return {
      baseVoice: 'standard',
      pitch: 1.0,
      speed: 1.0,
      tone: 'neutral',
      accent: 'standard',
      ...voiceConfig
    };
  }

  generateCacheKey(text, voiceConfig, emotionalState, options) {
    const keyData = {
      text,
      voiceConfig,
      emotionalState,
      options: {
        provider: options.provider,
        quality: options.quality,
        realtime: options.realtime
      }
    };

    return require('crypto')
      .createHash('md5')
      .update(JSON.stringify(keyData))
      .digest('hex');
  }

  cacheAudio(key, audioBuffer) {
    this.audioCache.set(key, {
      buffer: audioBuffer,
      timestamp: Date.now(),
      size: audioBuffer.length
    });

    // Check cache size limit
    if (this.audioCache.size > this.options.maxCacheSize) {
      this.cleanupCache();
    }
  }

  cleanupCache() {
    const entries = Array.from(this.audioCache.entries());
    entries.sort((a, b) => a[1].timestamp - b[1].timestamp);

    // Remove oldest 25% of entries
    const toRemove = Math.floor(entries.length * 0.25);
    for (let i = 0; i < toRemove; i++) {
      this.audioCache.delete(entries[i][0]);
    }
  }

  startCacheCleanup() {
    this.cacheCleanupInterval = setInterval(() => {
      const now = Date.now();
      const maxAge = 24 * 60 * 60 * 1000; // 24 hours

      for (const [key, value] of this.audioCache) {
        if (now - value.timestamp > maxAge) {
          this.audioCache.delete(key);
        }
      }
    }, 60 * 60 * 1000); // Check every hour
  }

  createVoiceProfile(config) {
    const profileKey = `${config.race}_${config.gender}_${config.socialClass || 'custom'}`;
    this.voiceProfiles.set(profileKey, {
      baseVoice: config.baseVoice || 'standard',
      pitch: config.pitch || 1.0,
      speed: config.speed || 1.0,
      tone: config.tone || 'neutral',
      accent: config.accent || 'standard',
      characteristics: config.characteristics || [],
      ...config
    });

    return this.voiceProfiles.get(profileKey);
  }

  createAccentPattern(name, pattern) {
    this.accentPatterns.set(name, {
      vowelShifts: pattern.vowelShifts || {},
      consonantModifications: pattern.consonantModifications || {},
      rhythm: pattern.rhythm || 'normal',
      melody: pattern.melody || 'neutral',
      commonPhrases: pattern.commonPhrases || []
    });
  }

  // API Methods
  getAvailableVoices() {
    return Array.from(this.voiceProfiles.keys());
  }

  getAvailableAccents() {
    return Array.from(this.accentPatterns.keys());
  }

  getCacheStats() {
    const totalSize = Array.from(this.audioCache.values())
      .reduce((sum, entry) => sum + entry.size, 0);

    return {
      entries: this.audioCache.size,
      totalSize: totalSize,
      averageSize: this.audioCache.size > 0 ? totalSize / this.audioCache.size : 0,
      oldestEntry: this.audioCache.size > 0 ?
        Math.min(...Array.from(this.audioCache.values()).map(e => e.timestamp)) : null
    };
  }

  clearCache() {
    this.audioCache.clear();
    this.emit('cacheCleared', { timestamp: new Date().toISOString() });
  }

  getProviderStatus() {
    const status = {};
    for (const [name, provider] of Object.entries(this.providers)) {
      status[name] = {
        available: provider !== null,
        configured: provider !== null && provider !== undefined
      };
    }
    return status;
  }

  stop() {
    if (this.cacheCleanupInterval) {
      clearInterval(this.cacheCleanupInterval);
    }
    this.audioCache.clear();
    this.processingQueue = [];
  }
}

module.exports = DynamicVoiceSynthesisEngine;