/**
 * DMlogn8n Voice Chat System Entry Point
 * Main export for the sophisticated voice chat system with spatial audio
 */

export { VoiceChatSystem } from './core/VoiceChatSystem.js';
export { WebRTCManager } from './webrtc/WebRTCManager.js';
export { SpatialAudioEngine } from './spatial-audio/SpatialAudioEngine.js';
export { VoiceProcessor } from './voice-processing/VoiceProcessor.js';
export { GameAudioIntegrator } from './game-integration/GameAudioIntegrator.js';
export { MobileVoiceAdapter } from './mobile/MobileVoiceAdapter.js';

// Voice processing components
export { VoiceActivityDetector } from './voice-processing/VoiceActivityDetector.js';
export { NoiseSuppressor } from './voice-processing/NoiseSuppressor.js';
export { CharacterVoiceFilter } from './voice-processing/CharacterVoiceFilter.js';
export { SpeechTranscriber } from './voice-processing/SpeechTranscriber.js';

// Spatial audio components
export { AudioPositionTracker } from './spatial-audio/AudioPositionTracker.js';
export { RoomAcousticsSimulator } from './spatial-audio/RoomAcousticsSimulator.js';
export { EnvironmentalAudioEffects } from './spatial-audio/EnvironmentalAudioEffects.js';

// Game integration components
export { CombatSoundEffects } from './game-integration/CombatSoundEffects.js';
export { SpellAudioProcessor } from './game-integration/SpellAudioProcessor.js';
export { AmbientSoundManager } from './game-integration/AmbientSoundManager.js';

// Utilities
export { VoiceChatUtils } from './core/VoiceChatUtils.js';
export { AudioMetricsCollector } from './core/AudioMetricsCollector.js';

// Default configuration
export const defaultConfig = {
  // WebRTC settings
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' }
  ],

  // Audio quality settings
  audio: {
    sampleRate: 48000,
    channelCount: 2,
    bufferSize: 4096,
    maxLatency: 50,
    bitrate: 128000
  },

  // Spatial audio settings
  spatialAudio: {
    enabled: true,
    maxDistance: 100,
    rolloffFactor: 1.0,
    roomSize: 'medium',
    reverbLevel: 0.3,
    dopplerEffect: true
  },

  // Voice processing settings
  voiceProcessing: {
    noiseSuppression: true,
    echoCancellation: true,
    autoGainControl: true,
    voiceActivityDetection: true,
    compressionEnabled: true
  },

  // Character voice settings
  characterVoices: {
    dwarvish: { pitch: -0.3, formantShift: 0.8, resonance: 1.2 },
    elvish: { pitch: 0.2, formantShift: 1.1, resonance: 0.9 },
    orcish: { pitch: -0.5, formantShift: 0.7, resonance: 1.4 },
    human: { pitch: 0, formantShift: 1.0, resonance: 1.0 },
    draconic: { pitch: 0.4, formantShift: 1.3, resonance: 1.1 }
  },

  // Game integration settings
  gameIntegration: {
    syncWithCombat: true,
    spellAudioFeedback: true,
    ambientSounds: true,
    musicIntegration: true,
    crossPortalSync: true
  },

  // Mobile settings
  mobile: {
    enabled: true,
    optimizedCodecs: true,
    adaptiveBitrate: true,
    batteryOptimization: true
  }
};

/**
 * Create a new Voice Chat System instance with default configuration
 */
export function createVoiceChatSystem(config = {}) {
  const mergedConfig = {
    ...defaultConfig,
    ...config,
    audio: { ...defaultConfig.audio, ...config.audio },
    spatialAudio: { ...defaultConfig.spatialAudio, ...config.spatialAudio },
    voiceProcessing: { ...defaultConfig.voiceProcessing, ...config.voiceProcessing },
    characterVoices: { ...defaultConfig.characterVoices, ...config.characterVoices },
    gameIntegration: { ...defaultConfig.gameIntegration, ...config.gameIntegration },
    mobile: { ...defaultConfig.mobile, ...config.mobile }
  };

  return new VoiceChatSystem(mergedConfig);
}

/**
 * Voice Chat System Factory for different use cases
 */
export const VoiceChatFactory = {
  /**
   * Create system for small groups (2-4 players)
   */
  createForSmallGroup(config = {}) {
    return createVoiceChatSystem({
      ...config,
      spatialAudio: {
        ...defaultConfig.spatialAudio,
        maxDistance: 50,
        roomSize: 'small'
      }
    });
  },

  /**
   * Create system for large groups (5+ players)
   */
  createForLargeGroup(config = {}) {
    return createVoiceChatSystem({
      ...config,
      spatialAudio: {
        ...defaultConfig.spatialAudio,
        maxDistance: 150,
        roomSize: 'large'
      },
      voiceProcessing: {
        ...defaultConfig.voiceProcessing,
        compressionEnabled: true
      }
    });
  },

  /**
   * Create system optimized for mobile
   */
  createForMobile(config = {}) {
    return createVoiceChatSystem({
      ...config,
      audio: {
        ...defaultConfig.audio,
        sampleRate: 16000, // Lower for mobile
        bufferSize: 2048
      },
      mobile: {
        ...defaultConfig.mobile,
        optimizedCodecs: true,
        adaptiveBitrate: true
      }
    });
  },

  /**
   * Create system for professional streaming
   */
  createForStreaming(config = {}) {
    return createVoiceChatSystem({
      ...config,
      audio: {
        ...defaultConfig.audio,
        sampleRate: 48000,
        bitrate: 256000
      },
      voiceProcessing: {
        ...defaultConfig.voiceProcessing,
        noiseSuppression: true,
        autoGainControl: true
      }
    });
  }
};

// Version information
export const VERSION = '1.0.0';

// System compatibility check
export function checkCompatibility() {
  const checks = {
    webRTC: !!(window.RTCPeerConnection || window.webkitRTCPeerConnection),
    webAudio: !!(window.AudioContext || window.webkitAudioContext),
    mediaDevices: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
    audioWorklet: !!(window.AudioContext && window.AudioContext.prototype.audioWorklet)
  };

  return {
    isCompatible: Object.values(checks).every(Boolean),
    checks,
    recommendations: getCompatibilityRecommendations(checks)
  };
}

function getCompatibilityRecommendations(checks) {
  const recommendations = [];

  if (!checks.webRTC) {
    recommendations.push('WebRTC is not supported. Consider using a modern browser like Chrome, Firefox, or Safari.');
  }

  if (!checks.webAudio) {
    recommendations.push('Web Audio API is not supported. Audio processing features will be limited.');
  }

  if (!checks.mediaDevices) {
    recommendations.push('MediaDevices API is not supported. Microphone access will not work.');
  }

  if (!checks.audioWorklet) {
    recommendations.push('AudioWorklet is not supported. Advanced audio processing will run on the main thread, which may affect performance.');
  }

  return recommendations;
}