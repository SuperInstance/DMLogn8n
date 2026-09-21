/**
 * Speech Transcriber - Real-time speech-to-text transcription and translation
 * Provides automatic speech recognition with multiple language support
 */

export class SpeechTranscriber {
  constructor(config = {}) {
    this.config = {
      language: 'en-US',
      continuous: true,
      interimResults: true,
      maxAlternatives: 1,
      grammars: [],
      enhanced: true,
      translationEnabled: false,
      targetLanguages: ['es', 'fr', 'de', 'ja', 'zh'],
      ...config
    };

    // Speech Recognition
    this.recognition = null;
    this.isListening = false;
    this.finalTranscript = '';
    this.interimTranscript = '';

    // Translation
    this.translator = null;
    this.translationCache = new Map();

    // Voice commands
    this.commandPatterns = new Map();
    this.commandHandlers = new Map();

    // Processing state
    this.state = {
      isTranscribing: false,
      confidence: 0,
      lastResult: null,
      languageDetected: this.config.language
    };

    // Event system
    this.eventListeners = new Map();

    // Performance metrics
    this.metrics = {
      wordsPerMinute: 0,
      averageConfidence: 0,
      transcriptionLatency: 0,
      errorRate: 0
    };

    // Initialize speech recognition
    this.initializeSpeechRecognition();
  }

  /**
   * Initialize speech recognition
   */
  initializeSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      console.warn('Speech Recognition not supported in this browser');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();

    // Configure recognition
    this.recognition.continuous = this.config.continuous;
    this.recognition.interimResults = this.config.interimResults;
    this.recognition.maxAlternatives = this.config.maxAlternatives;
    this.recognition.lang = this.config.language;

    // Set up event handlers
    this.setupRecognitionHandlers();

    // Initialize translation if enabled
    if (this.config.translationEnabled) {
      this.initializeTranslation();
    }

    // Initialize voice commands
    this.initializeVoiceCommands();
  }

  /**
   * Set up speech recognition event handlers
   */
  setupRecognitionHandlers() {
    this.recognition.onstart = () => {
      this.state.isTranscribing = true;
      this.emit('transcriptionStarted');
    };

    this.recognition.onresult = (event) => {
      this.handleRecognitionResult(event);
    };

    this.recognition.onerror = (event) => {
      this.handleRecognitionError(event);
    };

    this.recognition.onend = () => {
      this.state.isTranscribing = false;
      this.emit('transcriptionEnded');
    };

    this.recognition.onspeechstart = () => {
      this.emit('speechDetected');
    };

    this.recognition.onspeechend = () => {
      this.emit('speechEnded');
    };

    this.recognition.onnomatch = () => {
      this.emit('noMatch');
    };
  }

  /**
   * Handle speech recognition results
   */
  handleRecognitionResult(event) {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const result = event.results[i];

      if (result.isFinal) {
        // Final result
        const transcript = result[0].transcript;
        const confidence = result[0].confidence;

        finalTranscript += transcript;

        // Update state
        this.state.lastResult = {
          transcript,
          confidence,
          isFinal: true,
          timestamp: Date.now()
        };

        this.state.confidence = confidence;

        // Emit final result
        this.emit('transcription', {
          text: transcript,
          confidence,
          isFinal: true,
          language: this.state.languageDetected
        });

        // Process for commands and translation
        this.processTranscription(transcript, true);

      } else {
        // Interim result
        interimTranscript += result[0].transcript;

        // Emit interim result
        this.emit('interimTranscription', {
          text: result[0].transcript,
          confidence: result[0].confidence,
          isFinal: false
        });
      }
    }

    // Update transcripts
    this.finalTranscript += finalTranscript;
    this.interimTranscript = interimTranscript;

    // Update metrics
    this.updateMetrics(finalTranscript);

    // Emit combined results
    if (finalTranscript || interimTranscript) {
      this.emit('transcriptionUpdate', {
        final: this.finalTranscript,
        interim: this.interimTranscript,
        combined: this.finalTranscript + this.interimTranscript
      });
    }
  }

  /**
   * Handle speech recognition errors
   */
  handleRecognitionError(event) {
    console.error('Speech recognition error:', event.error);

    const errorMap = {
      'no-speech': 'No speech detected',
      'audio-capture': 'Audio capture error',
      'not-allowed': 'Microphone access denied',
      'network': 'Network error',
      'service-not-allowed': 'Speech recognition service not allowed'
    };

    const errorMessage = errorMap[event.error] || event.error;

    this.emit('transcriptionError', {
      error: event.error,
      message: errorMessage,
      event
    });
  }

  /**
   * Start transcription
   */
  start() {
    if (!this.recognition) {
      this.emit('error', { message: 'Speech recognition not available' });
      return;
    }

    if (this.isListening) {
      return;
    }

    try {
      this.recognition.lang = this.config.language;
      this.recognition.start();
      this.isListening = true;

      this.emit('listeningStarted');
    } catch (error) {
      console.error('Failed to start speech recognition:', error);
      this.emit('error', { message: 'Failed to start speech recognition', error });
    }
  }

  /**
   * Stop transcription
   */
  stop() {
    if (!this.recognition || !this.isListening) {
      return;
    }

    this.recognition.stop();
    this.isListening = false;

    this.emit('listeningStopped');
  }

  /**
   * Abort transcription
   */
  abort() {
    if (!this.recognition || !this.isListening) {
      return;
    }

    this.recognition.abort();
    this.isListening = false;

    this.emit('listeningAborted');
  }

  /**
   * Process transcription for commands and translation
   */
  async processTranscription(text, isFinal = false) {
    if (!text || text.trim().length === 0) return;

    // Check for voice commands
    const command = this.detectVoiceCommand(text);
    if (command) {
      this.executeVoiceCommand(command);
    }

    // Translate if enabled and text is final
    if (this.config.translationEnabled && isFinal) {
      await this.translateText(text);
    }

    // Emit processed text
    this.emit('textProcessed', {
      text,
      isFinal,
      command: command || null,
      timestamp: Date.now()
    });
  }

  /**
   * Detect voice commands in transcription
   */
  detectVoiceCommand(text) {
    const normalizedText = text.toLowerCase().trim();

    // Check against command patterns
    for (const [commandName, pattern] of this.commandPatterns) {
      if (pattern.test(normalizedText)) {
        const match = normalizedText.match(pattern);
        return {
          name: commandName,
          text,
          match,
          args: this.extractCommandArgs(match, commandName)
        };
      }
    }

    return null;
  }

  /**
   * Extract arguments from voice command
   */
  extractCommandArgs(match, commandName) {
    if (!match || match.length < 2) return [];

    // Different commands have different argument structures
    switch (commandName) {
      case 'roll':
        // Extract dice notation (e.g., "roll d20" or "roll 2d6+3")
        const diceNotation = match[1];
        return [diceNotation];

      case 'cast':
        // Extract spell name
        const spellName = match[1];
        return [spellName];

      case 'attack':
        // Extract target
        const target = match[1];
        return [target];

      case 'move':
        // Extract direction or distance
        const movement = match[1];
        return [movement];

      default:
        return match.slice(1);
    }
  }

  /**
   * Execute voice command
   */
  executeVoiceCommand(command) {
    const handler = this.commandHandlers.get(command.name);
    if (handler) {
      try {
        const result = handler(command.args, command);
        this.emit('commandExecuted', {
          command: command.name,
          args: command.args,
          result
        });
      } catch (error) {
        console.error('Error executing voice command:', error);
        this.emit('commandError', {
          command: command.name,
          args: command.args,
          error
        });
      }
    } else {
      this.emit('unknownCommand', {
        command: command.name,
        args: command.args
      });
    }
  }

  /**
   * Register voice command
   */
  registerCommand(name, pattern, handler) {
    this.commandPatterns.set(name, new RegExp(pattern, 'i'));
    this.commandHandlers.set(name, handler);

    this.emit('commandRegistered', { name, pattern });
  }

  /**
   * Unregister voice command
   */
  unregisterCommand(name) {
    this.commandPatterns.delete(name);
    this.commandHandlers.delete(name);

    this.emit('commandUnregistered', { name });
  }

  /**
   * Initialize default voice commands
   */
  initializeVoiceCommands() {
    // Dice rolling command
    this.registerCommand(
      'roll',
      'roll\\s+(d\\d+|\\d+d\\d+(?:[+-]\\d+)?)',
      (args) => {
        const notation = args[0];
        return this.parseDiceNotation(notation);
      }
    );

    // Spell casting command
    this.registerCommand(
      'cast',
      'cast\\s+(.+)',
      (args) => {
        const spellName = args[0];
        return { action: 'castSpell', spell: spellName };
      }
    );

    // Attack command
    this.registerCommand(
      'attack',
      'attack\\s+(.+)',
      (args) => {
        const target = args[0];
        return { action: 'attack', target };
      }
    );

    // Movement command
    this.registerCommand(
      'move',
      'move\\s+(.+)',
      (args) => {
        const movement = args[0];
        return { action: 'move', movement };
      }
    );

    // System commands
    this.registerCommand(
      'mute',
      'mute',
      () => ({ action: 'mute' })
    );

    this.registerCommand(
      'unmute',
      'unmute',
      () => ({ action: 'unmute' })
    );

    this.registerCommand(
      'stop',
      'stop',
      () => ({ action: 'stopListening' })
    );

    // Character voice commands
    this.registerCommand(
      'voice',
      'voice\\s+(\\w+)',
      (args) => {
        const character = args[0];
        return { action: 'changeVoice', character };
      }
    );
  }

  /**
   * Parse dice notation
   */
  parseDiceNotation(notation) {
    const match = notation.match(/(\d*)d(\d+)(?:([+-]\d+))?/);
    if (!match) return null;

    const numDice = parseInt(match[1]) || 1;
    const numSides = parseInt(match[2]);
    const modifier = match[3] ? parseInt(match[3]) : 0;

    // Roll dice
    let total = modifier;
    const rolls = [];

    for (let i = 0; i < numDice; i++) {
      const roll = Math.floor(Math.random() * numSides) + 1;
      rolls.push(roll);
      total += roll;
    }

    return {
      action: 'rollDice',
      notation,
      rolls,
      total,
      modifier
    };
  }

  /**
   * Initialize translation service
   */
  initializeTranslation() {
    // Initialize translation service (would use actual translation API)
    this.translator = {
      translate: async (text, targetLang) => {
        // Placeholder for actual translation
        return `[Translated to ${targetLang}] ${text}`;
      }
    };
  }

  /**
   * Translate text
   */
  async translateText(text) {
    if (!this.translator) return;

    const translations = {};

    for (const targetLang of this.config.targetLanguages) {
      try {
        const cacheKey = `${text}-${targetLang}`;
        let translation = this.translationCache.get(cacheKey);

        if (!translation) {
          translation = await this.translator.translate(text, targetLang);
          this.translationCache.set(cacheKey, translation);
        }

        translations[targetLang] = translation;
      } catch (error) {
        console.error(`Translation error for ${targetLang}:`, error);
      }
    }

    this.emit('translation', {
      originalText: text,
      translations,
      timestamp: Date.now()
    });
  }

  /**
   * Set language
   */
  setLanguage(language) {
    this.config.language = language;
    if (this.recognition) {
      this.recognition.lang = language;
    }

    this.emit('languageChanged', { language });
  }

  /**
   * Get supported languages
   */
  getSupportedLanguages() {
    // Return list of supported languages for speech recognition
    return [
      { code: 'en-US', name: 'English (US)' },
      { code: 'en-GB', name: 'English (UK)' },
      { code: 'es-ES', name: 'Spanish' },
      { code: 'fr-FR', name: 'French' },
      { code: 'de-DE', name: 'German' },
      { code: 'it-IT', name: 'Italian' },
      { code: 'pt-BR', name: 'Portuguese (Brazil)' },
      { code: 'ru-RU', name: 'Russian' },
      { code: 'ja-JP', name: 'Japanese' },
      { code: 'ko-KR', name: 'Korean' },
      { code: 'zh-CN', name: 'Chinese (Simplified)' }
    ];
  }

  /**
   * Update performance metrics
   */
  updateMetrics(transcript) {
    if (!transcript) return;

    // Calculate words per minute
    const words = transcript.trim().split(/\s+/).length;
    const timeMinutes = 1 / 60; // Assume current measurement window
    this.metrics.wordsPerMinute = words / timeMinutes;

    // Update average confidence
    if (this.state.confidence > 0) {
      this.metrics.averageConfidence =
        (this.metrics.averageConfidence + this.state.confidence) / 2;
    }
  }

  /**
   * Get metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      state: { ...this.state },
      isListening: this.isListening,
      finalTranscriptLength: this.finalTranscript.length,
      translationCacheSize: this.translationCache.size
    };
  }

  /**
   * Clear transcripts
   */
  clearTranscripts() {
    this.finalTranscript = '';
    this.interimTranscript = '';

    this.emit('transcriptsCleared');
  }

  /**
   * Export transcription data
   */
  exportTranscriptionData() {
    return {
      finalTranscript: this.finalTranscript,
      config: { ...this.config },
      metrics: this.getMetrics(),
      registeredCommands: Array.from(this.commandPatterns.keys()),
      timestamp: Date.now()
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
          console.error(`Error in speech transcriber event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Cleanup speech transcriber
   */
  cleanup() {
    if (this.recognition && this.isListening) {
      this.recognition.stop();
    }

    this.recognition = null;
    this.isListening = false;

    // Clear data
    this.finalTranscript = '';
    this.interimTranscript = '';
    this.translationCache.clear();
    this.commandPatterns.clear();
    this.commandHandlers.clear();
    this.eventListeners.clear();
  }
}