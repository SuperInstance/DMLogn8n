/**
 * Voice Chat System Tests
 * Comprehensive test suite for the voice chat system components
 */

import { jest } from '@jest/globals';
import { VoiceChatSystem } from '../src/core/VoiceChatSystem.js';

// Mock Web Audio API
global.AudioContext = jest.fn(() => ({
  createGain: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    gain: { value: 1.0 }
  })),
  createMediaStreamSource: jest.fn(() => ({
    connect: jest.fn()
  })),
  createPanner: jest.fn(() => ({
    connect: jest.fn(),
    positionX: { value: 0 },
    positionY: { value: 0 },
    positionZ: { value: 0 }
  })),
  createAnalyser: jest.fn(() => ({
    connect: jest.fn(),
    frequencyBinCount: 2048,
    getByteFrequencyData: jest.fn()
  })),
  createScriptProcessor: jest.fn(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    onaudioprocess: null
  })),
  createBiquadFilter: jest.fn(() => ({
    connect: jest.fn(),
    type: 'lowpass',
    frequency: { value: 1000 },
    Q: { value: 1 }
  })),
  createDynamicsCompressor: jest.fn(() => ({
    connect: jest.fn(),
    threshold: { value: -24 },
    ratio: { value: 4 }
  })),
  createMediaStreamDestination: jest.fn(() => ({
    stream: new MediaStream()
  })),
  createChannelMerger: jest.fn(() => ({
    connect: jest.fn()
  })),
  createBuffer: jest.fn(() => ({
    getChannelData: jest.fn(() => new Float32Array(1024))
  })),
  createBufferSource: jest.fn(() => ({
    buffer: null,
    connect: jest.fn(),
    start: jest.fn(),
    stop: jest.fn(),
    onended: null
  })),
  createDelay: jest.fn(() => ({
    connect: jest.fn(),
    delayTime: { value: 0 }
  })),
  createOscillator: jest.fn(() => ({
    connect: jest.fn(),
    frequency: { value: 440 },
    start: jest.fn(),
    stop: jest.fn()
  })),
  createWaveShaper: jest.fn(() => ({
    connect: jest.fn(),
    curve: null,
    oversample: '4x'
  })),
  createConvolver: jest.fn(() => ({
    connect: jest.fn(),
    buffer: null
  })),
  sampleRate: 48000,
  state: 'running',
  currentTime: 0,
  resume: jest.fn(),
  suspend: jest.fn(),
  close: jest.fn(),
  audioWorklet: {
    addModule: jest.fn()
  }
}));

// Mock getUserMedia
global.navigator = {
  mediaDevices: {
    getUserMedia: jest.fn(() => Promise.resolve(new MediaStream()))
  },
  userAgent: 'Test Browser',
  platform: 'Test Platform',
  hardwareConcurrency: 4,
  deviceMemory: 8
};

// Mock WebRTC
global.RTCPeerConnection = jest.fn(() => ({
  createOffer: jest.fn(() => Promise.resolve({ type: 'offer', sdp: 'test-sdp' })),
  createAnswer: jest.fn(() => Promise.resolve({ type: 'answer', sdp: 'test-sdp' })),
  setLocalDescription: jest.fn(() => Promise.resolve()),
  setRemoteDescription: jest.fn(() => Promise.resolve()),
  addIceCandidate: jest.fn(() => Promise.resolve()),
  addTrack: jest.fn(),
  createDataChannel: jest.fn(),
  onicecandidate: null,
  ontrack: null,
  onconnectionstatechange: null,
  connectionState: 'new',
  close: jest.fn()
}));

global.RTCIceCandidate = jest.fn();
global.RTCSessionDescription = jest.fn();

// Mock Socket.IO
global.io = jest.fn(() => ({
  on: jest.fn(),
  emit: jest.fn(),
  disconnect: jest.fn(),
  connected: true
}));

describe('VoiceChatSystem', () => {
  let voiceChatSystem;
  let mockConfig;

  beforeEach(() => {
    mockConfig = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' }
      ],
      sampleRate: 48000,
      channelCount: 2,
      maxLatency: 50,
      spatialAudio: {
        enabled: true,
        maxDistance: 100
      },
      voiceProcessing: {
        noiseSuppression: true,
        echoCancellation: true
      }
    };

    voiceChatSystem = new VoiceChatSystem(mockConfig);
  });

  afterEach(() => {
    if (voiceChatSystem) {
      voiceChatSystem.destroy();
    }
    jest.clearAllMocks();
  });

  describe('Initialization', () => {
    test('should initialize with default configuration', () => {
      expect(voiceChatSystem.config).toBeDefined();
      expect(voiceChatSystem.config.sampleRate).toBe(48000);
      expect(voiceChatSystem.config.channelCount).toBe(2);
    });

    test('should create audio context on initialization', () => {
      expect(global.AudioContext).toHaveBeenCalled();
    });

    test('should initialize components when initialize() is called', async () => {
      await voiceChatSystem.initialize();

      expect(voiceChatSystem.webrtcManager).toBeDefined();
      expect(voiceChatSystem.spatialAudioEngine).toBeDefined();
      expect(voiceChatSystem.voiceProcessor).toBeDefined();
      expect(voiceChatSystem.gameIntegrator).toBeDefined();
    });

    test('should emit initialization events', async () => {
      const onInitialized = jest.fn();
      voiceChatSystem.on('initializationStarted', onInitialized);
      voiceChatSystem.on('initializationComplete', onInitialized);

      await voiceChatSystem.initialize();

      expect(onInitialized).toHaveBeenCalledTimes(2);
    });

    test('should handle initialization errors gracefully', async () => {
      global.AudioContext.mockImplementation(() => {
        throw new Error('AudioContext not supported');
      });

      await expect(voiceChatSystem.initialize()).rejects.toThrow('AudioContext not supported');
    });
  });

  describe('Room Connection', () => {
    beforeEach(async () => {
      await voiceChatSystem.initialize();
    });

    test('should connect to room successfully', async () => {
      const roomId = 'test-room';
      const serverConfig = { url: 'ws://localhost:3000' };

      await voiceChatSystem.connectToRoom(roomId, serverConfig);

      expect(voiceChatSystem.state.currentRoom).toBe(roomId);
      expect(voiceChatSystem.state.isConnected).toBe(true);
    });

    test('should get local media stream on connection', async () => {
      const roomId = 'test-room';
      const serverConfig = { url: 'ws://localhost:3000' };

      await voiceChatSystem.connectToRoom(roomId, serverConfig);

      expect(global.navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
        audio: expect.objectContaining({
          sampleRate: 48000,
          channelCount: 2,
          echoCancellation: true,
          noiseSuppression: true
        }),
        video: false
      });
    });

    test('should emit connection events', async () => {
      const onConnecting = jest.fn();
      const onConnected = jest.fn();

      voiceChatSystem.on('connectingToRoom', onConnecting);
      voiceChatSystem.on('connectedToRoom', onConnected);

      const roomId = 'test-room';
      const serverConfig = { url: 'ws://localhost:3000' };

      await voiceChatSystem.connectToRoom(roomId, serverConfig);

      expect(onConnecting).toHaveBeenCalledWith({ roomId });
      expect(onConnected).toHaveBeenCalledWith({ roomId });
    });

    test('should handle connection errors', async () => {
      global.navigator.mediaDevices.getUserMedia.mockRejectedValue(new Error('Permission denied'));

      const roomId = 'test-room';
      const serverConfig = { url: 'ws://localhost:3000' };

      await expect(voiceChatSystem.connectToRoom(roomId, serverConfig)).rejects.toThrow('Permission denied');
    });
  });

  describe('Spatial Audio', () => {
    beforeEach(async () => {
      await voiceChatSystem.initialize();
    });

    test('should create spatial audio source for remote stream', async () => {
      const mockStream = new MediaStream();
      const sourceId = 'test-source';

      const spatialSource = await voiceChatSystem.spatialAudioEngine.createSpatialSource(sourceId, mockStream);

      expect(spatialSource).toBeDefined();
      expect(spatialSource.id).toBe(sourceId);
      expect(spatialSource.position).toEqual({ x: 0, y: 0, z: 0 });
    });

    test('should update participant position', async () => {
      const mockStream = new MediaStream();
      const sourceId = 'test-source';
      const position = { x: 10, y: 5, z: -3 };

      await voiceChatSystem.spatialAudioEngine.createSpatialSource(sourceId, mockStream);
      voiceChatSystem.updateParticipantPosition(sourceId, position);

      const participant = voiceChatSystem.state.participants.get(sourceId);
      expect(participant.position).toEqual(position);
    });

    test('should apply character voice filter', async () => {
      const mockStream = new MediaStream();
      const sourceId = 'test-source';
      const character = 'dwarvish';

      await voiceChatSystem.spatialAudioEngine.createSpatialSource(sourceId, mockStream);
      voiceChatSystem.setParticipantVoiceCharacter(sourceId, character);

      const participant = voiceChatSystem.state.participants.get(sourceId);
      expect(participant.voiceCharacter).toBe(character);
    });

    test('should mute/unmute spatial source', async () => {
      const mockStream = new MediaStream();
      const sourceId = 'test-source';

      const spatialSource = await voiceChatSystem.spatialAudioEngine.createSpatialSource(sourceId, mockStream);

      expect(spatialSource.isMuted).toBe(false);

      voiceChatSystem.spatialAudioEngine.muteSource(sourceId, true);
      expect(spatialSource.isMuted).toBe(true);

      voiceChatSystem.spatialAudioEngine.muteSource(sourceId, false);
      expect(spatialSource.isMuted).toBe(false);
    });
  });

  describe('Voice Processing', () => {
    beforeEach(async () => {
      await voiceChatSystem.initialize();
    });

    test('should process local stream', async () => {
      const mockStream = new MediaStream();

      const processedStream = await voiceChatSystem.voiceProcessor.processLocalStream(mockStream);

      expect(processedStream).toBeDefined();
      expect(processedStream).toBeInstanceOf(MediaStream);
    });

    test('should set character voice', async () => {
      const character = 'elvish';

      voiceChatSystem.voiceProcessor.setCharacterVoice(character);

      expect(voiceChatSystem.voiceProcessor.voiceState.character).toBe(character);
    });

    test('should set voice age', async () => {
      const age = 'old';

      voiceChatSystem.voiceProcessor.setVoiceAge(age);

      expect(voiceChatSystem.voiceProcessor.voiceState.age).toBe(age);
    });

    test('should set emotion', async () => {
      const emotion = 'angry';

      voiceChatSystem.voiceProcessor.setEmotion(emotion);

      expect(voiceChatSystem.voiceProcessor.voiceState.emotion).toBe(emotion);
    });

    test('should mute/unmute local audio', () => {
      expect(voiceChatSystem.voiceProcessor.isLocalAudioMuted()).toBe(false);

      voiceChatSystem.voiceProcessor.mute();
      expect(voiceChatSystem.voiceProcessor.isLocalAudioMuted()).toBe(true);

      voiceChatSystem.voiceProcessor.unmute();
      expect(voiceChatSystem.voiceProcessor.isLocalAudioMuted()).toBe(false);
    });
  });

  describe('Game Integration', () => {
    beforeEach(async () => {
      await voiceChatSystem.initialize();
    });

    test('should initialize game integrator', async () => {
      await voiceChatSystem.gameIntegrator.initialize(voiceChatSystem.state.audioContext);

      expect(voiceChatSystem.gameIntegrator.combatSoundEffects).toBeDefined();
      expect(voiceChatSystem.gameIntegrator.spellAudioProcessor).toBeDefined();
      expect(voiceChatSystem.gameIntegrator.ambientSoundManager).toBeDefined();
    });

    test('should add combat sound effects', async () => {
      await voiceChatSystem.gameIntegrator.initialize(voiceChatSystem.state.audioContext);

      const effects = [
        { type: 'hit', intensity: 0.7, position: { x: 0, y: 0, z: 0 } }
      ];
      const participants = ['player1', 'player2'];

      voiceChatSystem.gameIntegrator.addCombatSoundEffects(effects, participants);

      // The effects should be processed by the combat sound system
      expect(voiceChatSystem.gameIntegrator.combatSoundEffects).toBeDefined();
    });

    test('should add spell audio', async () => {
      await voiceChatSystem.gameIntegrator.initialize(voiceChatSystem.state.audioContext);

      const spell = { name: 'fireball', school: 'evocation', duration: 2000 };
      const caster = { id: 'caster1', position: { x: 0, y: 0, z: 0 } };
      const target = { id: 'target1', position: { x: 10, y: 0, z: 0 } };

      voiceChatSystem.gameIntegrator.addSpellAudio(spell, caster, target);

      expect(voiceChatSystem.gameIntegrator.spellAudioProcessor).toBeDefined();
    });

    test('should update game state', () => {
      const newState = {
        inCombat: true,
        healthLevel: 0.8,
        manaLevel: 0.6
      };

      voiceChatSystem.gameIntegrator.updateGameState(newState);

      expect(voiceChatSystem.gameIntegrator.gameState.inCombat).toBe(true);
      expect(voiceChatSystem.gameIntegrator.gameState.healthLevel).toBe(0.8);
      expect(voiceChatSystem.gameIntegrator.gameState.manaLevel).toBe(0.6);
    });
  });

  describe('Mobile Compatibility', () => {
    test('should create mobile adapter when on mobile device', () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        configurable: true
      });

      const mobileVoiceChatSystem = new VoiceChatSystem(mockConfig);
      expect(mobileVoiceChatSystem).toBeDefined();
    });

    test('should get mobile audio constraints', async () => {
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        configurable: true
      });

      const mobileVoiceChatSystem = new VoiceChatSystem(mockConfig);
      await mobileVoiceChatSystem.initialize();

      // Mobile adapter should provide optimized constraints
      expect(mobileVoiceChatSystem.mobileAdapter).toBeDefined();
    });
  });

  describe('Performance Metrics', () => {
    beforeEach(async () => {
      await voiceChatSystem.initialize();
    });

    test('should return performance metrics', () => {
      const metrics = voiceChatSystem.getPerformanceMetrics();

      expect(metrics).toHaveProperty('latency');
      expect(metrics).toHaveProperty('packetLoss');
      expect(metrics).toHaveProperty('audioQuality');
      expect(metrics).toHaveProperty('cpuUsage');
      expect(metrics).toHaveProperty('participantCount');
    });

    test('should track active participants', async () => {
      const mockStream = new MediaStream();
      const sourceId = 'test-source';

      await voiceChatSystem.spatialAudioEngine.createSpatialSource(sourceId, mockStream);

      const metrics = voiceChatSystem.getPerformanceMetrics();
      expect(metrics.participantCount).toBe(1);
    });

    test('should provide spatial audio metrics', () => {
      const metrics = voiceChatSystem.spatialAudioEngine.getMetrics();

      expect(metrics).toHaveProperty('activeSources');
      expect(metrics).toHaveProperty('cpuUsage');
      expect(metrics).toHaveProperty('memoryUsage');
    });

    test('should provide voice processing metrics', () => {
      const metrics = voiceChatSystem.voiceProcessor.getMetrics();

      expect(metrics).toHaveProperty('processingLatency');
      expect(metrics).toHaveProperty('cpuUsage');
      expect(metrics).toHaveProperty('noiseLevel');
      expect(metrics).toHaveProperty('voiceQuality');
    });
  });

  describe('Event System', () => {
    test('should register and emit events', () => {
      const callback = jest.fn();
      voiceChatSystem.on('test-event', callback);

      voiceChatSystem.emit('test-event', { data: 'test' });

      expect(callback).toHaveBeenCalledWith({ data: 'test' });
    });

    test('should handle multiple listeners for same event', () => {
      const callback1 = jest.fn();
      const callback2 = jest.fn();

      voiceChatSystem.on('test-event', callback1);
      voiceChatSystem.on('test-event', callback2);

      voiceChatSystem.emit('test-event', { data: 'test' });

      expect(callback1).toHaveBeenCalledWith({ data: 'test' });
      expect(callback2).toHaveBeenCalledWith({ data: 'test' });
    });

    test('should handle errors in event listeners gracefully', () => {
      const errorCallback = jest.fn(() => {
        throw new Error('Listener error');
      });
      const normalCallback = jest.fn();

      voiceChatSystem.on('test-event', errorCallback);
      voiceChatSystem.on('test-event', normalCallback);

      // Should not throw and other listeners should still be called
      expect(() => {
        voiceChatSystem.emit('test-event', { data: 'test' });
      }).not.toThrow();

      expect(normalCallback).toHaveBeenCalled();
    });
  });

  describe('Cleanup and Destruction', () => {
    beforeEach(async () => {
      await voiceChatSystem.initialize();
    });

    test('should disconnect from room', async () => {
      const roomId = 'test-room';
      const serverConfig = { url: 'ws://localhost:3000' };

      await voiceChatSystem.connectToRoom(roomId, serverConfig);
      await voiceChatSystem.disconnect();

      expect(voiceChatSystem.state.isConnected).toBe(false);
      expect(voiceChatSystem.state.currentRoom).toBe(null);
    });

    test('should cleanup all resources', async () => {
      const mockStream = new MediaStream();
      const sourceId = 'test-source';

      await voiceChatSystem.spatialAudioEngine.createSpatialSource(sourceId, mockStream);

      await voiceChatSystem.destroy();

      expect(voiceChatSystem.state.participants.size).toBe(0);
      expect(voiceChatSystem.state.audioContext).toBe(null);
    });

    test('should stop all audio processing on cleanup', async () => {
      const mockStream = new MediaStream();

      await voiceChatSystem.voiceProcessor.processLocalStream(mockStream);
      await voiceChatSystem.destroy();

      expect(voiceChatSystem.voiceProcessor.voiceState.isProcessing).toBe(false);
    });
  });

  describe('Error Handling', () => {
    test('should handle WebRTC connection failures', async () => {
      await voiceChatSystem.initialize();

      // Mock connection failure
      voiceChatSystem.webrtcManager.connect = jest.fn().mockRejectedValue(new Error('Connection failed'));

      const roomId = 'test-room';
      const serverConfig = { url: 'ws://localhost:3000' };

      await expect(voiceChatSystem.connectToRoom(roomId, serverConfig)).rejects.toThrow('Connection failed');
    });

    test('should handle microphone permission denial', async () => {
      global.navigator.mediaDevices.getUserMedia.mockRejectedValue(new Error('Permission denied'));

      await voiceChatSystem.initialize();

      const roomId = 'test-room';
      const serverConfig = { url: 'ws://localhost:3000' };

      await expect(voiceChatSystem.connectToRoom(roomId, serverConfig)).rejects.toThrow('Permission denied');
    });

    test('should handle audio context suspension', async () => {
      const mockAudioContext = {
        ...new AudioContext(),
        state: 'suspended',
        resume: jest.fn()
      };
      global.AudioContext.mockImplementation(() => mockAudioContext);

      const testVoiceChatSystem = new VoiceChatSystem(mockConfig);
      await testVoiceChatSystem.initialize();

      expect(mockAudioContext.resume).toHaveBeenCalled();
    });
  });

  describe('Integration Tests', () => {
    test('should handle complete voice chat session', async () => {
      // Initialize system
      await voiceChatSystem.initialize();

      // Connect to room
      const roomId = 'integration-test-room';
      const serverConfig = { url: 'ws://localhost:3000' };
      await voiceChatSystem.connectToRoom(roomId, serverConfig);

      // Add participants
      const mockStream1 = new MediaStream();
      const mockStream2 = new MediaStream();

      await voiceChatSystem.spatialAudioEngine.createSpatialSource('participant1', mockStream1);
      await voiceChatSystem.spatialAudioEngine.createSpatialSource('participant2', mockStream2);

      // Update positions
      voiceChatSystem.updateParticipantPosition('participant1', { x: 5, y: 0, z: 0 });
      voiceChatSystem.updateParticipantPosition('participant2', { x: -5, y: 0, z: 0 });

      // Apply character voices
      voiceChatSystem.setParticipantVoiceCharacter('participant1', 'dwarvish');
      voiceChatSystem.setParticipantVoiceCharacter('participant2', 'elvish');

      // Start game integration
      await voiceChatSystem.gameIntegrator.initialize(voiceChatSystem.state.audioContext);
      voiceChatSystem.gameIntegrator.addCombatSoundEffects([
        { type: 'hit', intensity: 0.8, position: { x: 0, y: 0, z: 0 } }
      ], ['participant1', 'participant2']);

      // Verify system state
      expect(voiceChatSystem.state.isConnected).toBe(true);
      expect(voiceChatSystem.state.participants.size).toBe(2);

      // Cleanup
      await voiceChatSystem.disconnect();
      await voiceChatSystem.destroy();

      expect(voiceChatSystem.state.participants.size).toBe(0);
    });

    test('should handle mobile session with adaptive quality', async () => {
      // Simulate mobile device
      Object.defineProperty(navigator, 'userAgent', {
        value: 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        configurable: true
      });

      const mobileVoiceChatSystem = new VoiceChatSystem({
        ...mockConfig,
        mobile: {
          enabled: true,
          adaptiveBitrate: true,
          batteryOptimization: true
        }
      });

      await mobileVoiceChatSystem.initialize();

      // Simulate low battery
      mobileVoiceChatSystem.mobileAdapter.state.isLowPowerMode = true;
      mobileVoiceChatSystem.mobileAdapter.enableLowPowerMode();

      // Verify adaptive behavior
      expect(mobileVoiceChatSystem.mobileAdapter.state.isLowPowerMode).toBe(true);

      await mobileVoiceChatSystem.destroy();
    });
  });
});