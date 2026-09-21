/**
 * DMlogn8n Voice Chat System - Core Architecture
 * Provides sophisticated voice chat with spatial audio for immersive gaming experiences
 */

import { WebRTCManager } from '../webrtc/WebRTCManager.js';
import { SpatialAudioEngine } from '../spatial-audio/SpatialAudioEngine.js';
import { VoiceProcessor } from '../voice-processing/VoiceProcessor.js';
import { GameAudioIntegrator } from '../game-integration/GameAudioIntegrator.js';
import { MobileVoiceAdapter } from '../mobile/MobileVoiceAdapter.js';

export class VoiceChatSystem {
  constructor(config = {}) {
    this.config = {
      // WebRTC Configuration
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ],

      // Audio Configuration
      sampleRate: 48000,
      channelCount: 2,
      bufferSize: 4096,
      maxLatency: 50, // ms

      // Spatial Audio Configuration
      spatialAudio: {
        enabled: true,
        maxDistance: 100,
        rolloffFactor: 1.0,
        roomSize: 'medium', // small, medium, large, hall
        reverbLevel: 0.3
      },

      // Voice Processing Configuration
      voiceProcessing: {
        noiseSuppression: true,
        echoCancellation: true,
        autoGainControl: true,
        voiceActivityDetection: true
      },

      // Game Integration
      gameIntegration: {
        syncWithCombat: true,
        spellAudioFeedback: true,
        ambientSounds: true,
        musicIntegration: true
      },

      ...config
    };

    // Core components
    this.webrtcManager = null;
    this.spatialAudioEngine = null;
    this.voiceProcessor = null;
    this.gameIntegrator = null;
    this.mobileAdapter = null;

    // State management
    this.state = {
      isConnected: false,
      isRecording: false,
      participants: new Map(),
      localStream: null,
      audioContext: null,
      currentRoom: null
    };

    // Event system
    this.eventListeners = new Map();
    this.audioWorklets = new Map();

    // Performance monitoring
    this.performance = {
      latency: 0,
      packetLoss: 0,
      audioQuality: 1.0,
      cpuUsage: 0
    };

    this.initializeAudioContext();
  }

  /**
   * Initialize the Web Audio API context
   */
  async initializeAudioContext() {
    try {
      this.state.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: this.config.sampleRate,
        latencyHint: 'interactive'
      });

      // Resume context if suspended (browser policy)
      if (this.state.audioContext.state === 'suspended') {
        await this.state.audioContext.resume();
      }

      this.emit('audioContextInitialized', { sampleRate: this.state.audioContext.sampleRate });
    } catch (error) {
      console.error('Failed to initialize audio context:', error);
      throw error;
    }
  }

  /**
   * Initialize all voice chat components
   */
  async initialize() {
    try {
      this.emit('initializationStarted');

      // Initialize core components
      this.webrtcManager = new WebRTCManager(this.config);
      this.spatialAudioEngine = new SpatialAudioEngine(this.state.audioContext, this.config.spatialAudio);
      this.voiceProcessor = new VoiceProcessor(this.state.audioContext, this.config.voiceProcessing);
      this.gameIntegrator = new GameAudioIntegrator(this.config.gameIntegration);

      // Check for mobile environment
      if (this.isMobileDevice()) {
        this.mobileAdapter = new MobileVoiceAdapter(this.config);
        await this.mobileAdapter.initialize();
      }

      // Set up component communication
      this.setupComponentCommunication();

      // Load audio worklets
      await this.loadAudioWorklets();

      this.emit('initializationComplete');
    } catch (error) {
      console.error('Voice chat system initialization failed:', error);
      this.emit('initializationError', error);
      throw error;
    }
  }

  /**
   * Set up communication between components
   */
  setupComponentCommunication() {
    // WebRTC events
    this.webrtcManager.on('streamAdded', this.handleRemoteStream.bind(this));
    this.webrtcManager.on('streamRemoved', this.handleStreamRemoved.bind(this));
    this.webrtcManager.on('connectionStateChange', this.handleConnectionStateChange.bind(this));

    // Voice processing events
    this.voiceProcessor.on('voiceActivity', this.handleVoiceActivity.bind(this));
    this.voiceProcessor.on('transcription', this.handleTranscription.bind(this));

    // Game integration events
    this.gameIntegrator.on('combatEvent', this.handleCombatEvent.bind(this));
    this.gameIntegrator.on('spellCast', this.handleSpellCast.bind(this));

    // Spatial audio events
    this.spatialAudioEngine.on('positionUpdate', this.handlePositionUpdate.bind(this));
  }

  /**
   * Load required audio worklets
   */
  async loadAudioWorklets() {
    const worklets = [
      'spatial-audio-processor.js',
      'voice-activity-detector.js',
      'noise-suppressor.js',
      'character-voice-filter.js'
    ];

    for (const worklet of worklets) {
      try {
        await this.state.audioContext.audioWorklet.addModule(`/worklets/${worklet}`);
        this.audioWorklets.set(worklet, true);
      } catch (error) {
        console.warn(`Failed to load audio worklet ${worklet}:`, error);
      }
    }
  }

  /**
   * Connect to a voice chat room
   */
  async connectToRoom(roomId, serverConfig) {
    try {
      this.emit('connectingToRoom', { roomId });

      // Initialize WebRTC connection
      await this.webrtcManager.connect(roomId, serverConfig);

      // Get user media
      await this.getLocalMediaStream();

      // Set up spatial audio
      this.spatialAudioEngine.initialize();

      this.state.currentRoom = roomId;
      this.state.isConnected = true;

      this.emit('connectedToRoom', { roomId });
    } catch (error) {
      console.error('Failed to connect to room:', error);
      this.emit('connectionError', error);
      throw error;
    }
  }

  /**
   * Get local media stream with audio constraints
   */
  async getLocalMediaStream() {
    try {
      const constraints = {
        audio: {
          sampleRate: this.config.sampleRate,
          channelCount: this.config.channelCount,
          echoCancellation: this.config.voiceProcessing.echoCancellation,
          noiseSuppression: this.config.voiceProcessing.noiseSuppression,
          autoGainControl: this.config.voiceProcessing.autoGainControl,
          latency: 0.01
        },
        video: false
      };

      // Apply mobile-specific constraints
      if (this.mobileAdapter) {
        Object.assign(constraints.audio, this.mobileAdapter.getAudioConstraints());
      }

      this.state.localStream = await navigator.mediaDevices.getUserMedia(constraints);

      // Process local audio through voice processor
      const processedStream = await this.voiceProcessor.processLocalStream(this.state.localStream);

      // Add to WebRTC manager
      this.webrtcManager.addLocalStream(processedStream);

      this.emit('localStreamReady', { stream: processedStream });
    } catch (error) {
      console.error('Failed to get local media stream:', error);
      throw error;
    }
  }

  /**
   * Handle remote stream from WebRTC
   */
  async handleRemoteStream(event) {
    const { participantId, stream } = event;

    try {
      // Create spatial audio source for remote participant
      const spatialSource = await this.spatialAudioEngine.createSpatialSource(
        participantId,
        stream
      );

      // Store participant info
      this.state.participants.set(participantId, {
        stream,
        spatialSource,
        position: { x: 0, y: 0, z: 0 },
        voiceCharacter: 'default'
      });

      this.emit('participantJoined', { participantId, stream });
    } catch (error) {
      console.error('Failed to handle remote stream:', error);
    }
  }

  /**
   * Handle stream removal
   */
  handleStreamRemoved(event) {
    const { participantId } = event;

    if (this.state.participants.has(participantId)) {
      const participant = this.state.participants.get(participantId);
      this.spatialAudioEngine.removeSpatialSource(participant.spatialSource);
      this.state.participants.delete(participantId);

      this.emit('participantLeft', { participantId });
    }
  }

  /**
   * Update participant position for spatial audio
   */
  updateParticipantPosition(participantId, position) {
    if (this.state.participants.has(participantId)) {
      const participant = this.state.participants.get(participantId);
      participant.position = position;

      this.spatialAudioEngine.updateSourcePosition(
        participant.spatialSource,
        position
      );
    }
  }

  /**
   * Set voice character for participant
   */
  setParticipantVoiceCharacter(participantId, character) {
    if (this.state.participants.has(participantId)) {
      const participant = this.state.participants.get(participantId);
      participant.voiceCharacter = character;

      this.voiceProcessor.applyCharacterFilter(
        participant.spatialSource,
        character
      );
    }
  }

  /**
   * Start/stop recording
   */
  async toggleRecording() {
    if (this.state.isRecording) {
      this.stopRecording();
    } else {
      await this.startRecording();
    }
  }

  async startRecording() {
    if (!this.state.localStream) {
      throw new Error('No local stream available');
    }

    this.state.isRecording = true;
    this.emit('recordingStarted');
  }

  stopRecording() {
    this.state.isRecording = false;
    this.emit('recordingStopped');
  }

  /**
   * Handle voice activity detection
   */
  handleVoiceActivity(event) {
    const { isActive, level } = event;

    // Update UI based on voice activity
    this.emit('voiceActivity', { isActive, level });

    // Could trigger push-to-talk or other features
  }

  /**
   * Handle speech transcription
   */
  handleTranscription(event) {
    const { text, confidence, participantId } = event;

    this.emit('transcription', { text, confidence, participantId });

    // Process for commands or translation
    this.processTranscription(text, participantId);
  }

  /**
   * Process transcription for commands or translation
   */
  processTranscription(text, participantId) {
    // Check for voice commands
    if (text.startsWith('/')) {
      this.processVoiceCommand(text, participantId);
    }

    // Trigger translation if needed
    // this.translateText(text, participantId);
  }

  /**
   * Handle combat events from game integration
   */
  handleCombatEvent(event) {
    const { type, participants, effects } = event;

    // Add combat sound effects to spatial audio
    this.gameIntegrator.addCombatSoundEffects(effects, participants);
  }

  /**
   * Handle spell casting events
   */
  handleSpellCast(event) {
    const { spell, caster, target } = event;

    // Add spell audio feedback
    this.gameIntegrator.addSpellAudio(spell, caster, target);
  }

  /**
   * Get system performance metrics
   */
  getPerformanceMetrics() {
    return {
      ...this.performance,
      participantCount: this.state.participants.size,
      audioContextState: this.state.audioContext?.state,
      webrtcConnections: this.webrtcManager?.getConnectionCount() || 0
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
          console.error(`Error in event listener for ${event}:`, error);
        }
      });
    }
  }

  /**
   * Check if running on mobile device
   */
  isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
  }

  /**
   * Disconnect from voice chat
   */
  async disconnect() {
    try {
      // Stop recording
      if (this.state.isRecording) {
        this.stopRecording();
      }

      // Stop local stream
      if (this.state.localStream) {
        this.state.localStream.getTracks().forEach(track => track.stop());
      }

      // Disconnect WebRTC
      if (this.webrtcManager) {
        await this.webrtcManager.disconnect();
      }

      // Clean up spatial audio
      if (this.spatialAudioEngine) {
        this.spatialAudioEngine.cleanup();
      }

      // Clean up voice processor
      if (this.voiceProcessor) {
        this.voiceProcessor.cleanup();
      }

      // Reset state
      this.state.isConnected = false;
      this.state.participants.clear();
      this.state.currentRoom = null;

      this.emit('disconnected');
    } catch (error) {
      console.error('Error during disconnect:', error);
    }
  }

  /**
   * Cleanup and destroy the voice chat system
   */
  async destroy() {
    await this.disconnect();

    if (this.state.audioContext) {
      await this.state.audioContext.close();
    }

    this.eventListeners.clear();
    this.audioWorklets.clear();
  }
}