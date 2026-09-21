/**
 * D&D Game Integration Example
 * Demonstrates how to integrate the voice chat system with a D&D game
 */

import { createVoiceChatSystem } from '../src/index.js';

class DNDVoiceIntegration {
  constructor(gameState) {
    this.gameState = gameState;
    this.voiceChat = null;
    this.participants = new Map();
    this.characterMap = new Map();

    // UI Elements
    this.ui = {
      voiceIndicator: document.getElementById('voice-indicator'),
      participantList: document.getElementById('participants'),
      pushToTalkBtn: document.getElementById('push-to-talk'),
      muteBtn: document.getElementById('mute-btn'),
      characterSelect: document.getElementById('character-voice')
    };

    // Initialize character mapping
    this.initializeCharacterMapping();

    // Setup UI handlers
    this.setupUIHandlers();
  }

  /**
   * Initialize character voice mapping
   */
  initializeCharacterMapping() {
    this.characterMap.set('human', 'human');
    this.characterMap.set('elf', 'elvish');
    this.characterMap.set('dwarf', 'dwarvish');
    this.characterMap.set('orc', 'orcish');
    this.characterMap.set('dragonborn', 'draconic');
    this.characterMap.set('halfling', 'halfling');
    this.characterMap.set('gnome', 'gnome');
    this.characterMap.set('tiefling', 'draconic'); // Similar vocal qualities
    this.characterMap.set('half-elf', 'elvish');
    this.characterMap.set('half-orc', 'orcish');
  }

  /**
   * Setup UI event handlers
   */
  setupUIHandlers() {
    // Push-to-talk
    if (this.ui.pushToTalkBtn) {
      this.ui.pushToTalkBtn.addEventListener('mousedown', () => this.startTalking());
      this.ui.pushToTalkBtn.addEventListener('mouseup', () => this.stopTalking());
      this.ui.pushToTalkBtn.addEventListener('touchstart', (e) => {
        e.preventDefault();
        this.startTalking();
      });
      this.ui.pushToTalkBtn.addEventListener('touchend', (e) => {
        e.preventDefault();
        this.stopTalking();
      });
    }

    // Mute toggle
    if (this.ui.muteBtn) {
      this.ui.muteBtn.addEventListener('click', () => this.toggleMute());
    }

    // Character voice selection
    if (this.ui.characterSelect) {
      this.ui.characterSelect.addEventListener('change', (e) => {
        this.setCharacterVoice(e.target.value);
      });
    }
  }

  /**
   * Initialize voice chat system
   */
  async initialize(roomId, serverConfig) {
    try {
      console.log('Initializing D&D voice chat integration...');

      // Create voice chat system with D&D specific configuration
      this.voiceChat = createVoiceChatSystem({
        spatialAudio: {
          enabled: true,
          maxDistance: 50, // 50 foot range for D&D
          roomSize: 'medium',
          dopplerEffect: true
        },
        voiceProcessing: {
          noiseSuppression: true,
          echoCancellation: true,
          voiceActivityDetection: true
        },
        gameIntegration: {
          syncWithCombat: true,
          spellAudioFeedback: true,
          ambientSounds: true
        }
      });

      // Initialize system
      await this.voiceChat.initialize();
      console.log('Voice chat system initialized');

      // Set up event handlers
      this.setupVoiceChatEvents();

      // Connect to voice room
      await this.voiceChat.connectToRoom(roomId, serverConfig);
      console.log('Connected to voice room:', roomId);

      // Initialize game audio integration
      await this.initializeGameAudio();

      // Setup player tracking
      this.setupPlayerTracking();

      console.log('D&D voice chat integration ready');
      return this.voiceChat;

    } catch (error) {
      console.error('Failed to initialize voice chat:', error);
      this.showError('Failed to initialize voice chat: ' + error.message);
      throw error;
    }
  }

  /**
   * Setup voice chat event handlers
   */
  setupVoiceChatEvents() {
    // Participant joined
    this.voiceChat.on('participantJoined', (data) => {
      console.log('Participant joined:', data.participantId);
      this.addParticipantToList(data.participantId);
      this.applyCharacterVoice(data.participantId);
    });

    // Participant left
    this.voiceChat.on('participantLeft', (data) => {
      console.log('Participant left:', data.participantId);
      this.removeParticipantFromList(data.participantId);
    });

    // Voice activity
    this.voiceChat.on('voiceActivity', (data) => {
      this.updateVoiceIndicator(data.isActive, data.level);
    });

    // Transcription
    this.voiceChat.on('transcription', (data) => {
      this.handleTranscription(data);
    });

    // Position updates
    this.voiceChat.on('positionUpdate', (data) => {
      this.updateParticipantPosition(data.participantId, data.position);
    });

    // Combat events
    this.voiceChat.on('combatSoundPlayed', (data) => {
      console.log('Combat sound played:', data.soundType);
    });

    // Spell events
    this.voiceChat.on('spellCast', (data) => {
      console.log('Spell cast:', data.spellName);
      this.handleSpellCast(data);
    });

    // Connection events
    this.voiceChat.on('connectedToRoom', () => {
      this.showStatus('Connected to voice chat', 'success');
    });

    this.voiceChat.on('connectionError', (error) => {
      this.showStatus('Connection error: ' + error.message, 'error');
    });
  }

  /**
   * Initialize game audio integration
   */
  async initializeGameAudio() {
    await this.voiceChat.gameIntegrator.initialize(this.voiceChat.state.audioContext);

    // Set up combat event handlers
    this.gameState.on('combatStarted', (combat) => {
      this.handleCombatStarted(combat);
    });

    this.gameState.on('combatEnded', () => {
      this.handleCombatEnded();
    });

    this.gameState.on('spellCast', (spellData) => {
      this.handleGameSpellCast(spellData);
    });

    this.gameState.on('environmentChanged', (environment) => {
      this.handleEnvironmentChange(environment);
    });
  }

  /**
   * Setup player position tracking
   */
  setupPlayerTracking() {
    // Track player positions from game state
    this.gameState.on('playerMoved', (data) => {
      const { playerId, position } = data;
      this.voiceChat.updateParticipantPosition(playerId, position);
    });

    // Update my own position
    this.gameState.on('myPositionChanged', (position) => {
      this.voiceChat.spatialAudioEngine.setListenerPosition(position);
    });
  }

  /**
   * Add participant to UI list
   */
  addParticipantToList(participantId) {
    const player = this.gameState.getPlayer(participantId);
    const li = document.createElement('li');
    li.id = `participant-${participantId}`;
    li.className = 'participant-item';

    const character = player ? player.character : null;
    const voiceType = character ? this.characterMap.get(character.race) : 'human';

    li.innerHTML = `
      <div class="participant-info">
        <span class="participant-name">${player ? player.name : participantId}</span>
        <span class="character-race">${character ? character.race : 'Unknown'}</span>
        <span class="voice-type">${voiceType}</span>
      </div>
      <div class="participant-status">
        <div class="voice-level" style="width: 0%"></div>
        <div class="speaking-indicator hidden">🔊</div>
      </div>
    `;

    if (this.ui.participantList) {
      this.ui.participantList.appendChild(li);
    }

    this.participants.set(participantId, {
      element: li,
      player,
      voiceType
    });
  }

  /**
   * Remove participant from UI list
   */
  removeParticipantFromList(participantId) {
    const participant = this.participants.get(participantId);
    if (participant && participant.element) {
      participant.element.remove();
    }
    this.participants.delete(participantId);
  }

  /**
   * Apply character voice to participant
   */
  applyCharacterVoice(participantId) {
    const participant = this.participants.get(participantId);
    if (!participant || !participant.player) return;

    const character = participant.player.character;
    const voiceType = this.characterMap.get(character.race) || 'human';

    this.voiceChat.setParticipantVoiceCharacter(participantId, voiceType);
    participant.voiceType = voiceType;
  }

  /**
   * Update voice indicator UI
   */
  updateVoiceIndicator(isActive, level) {
    if (this.ui.voiceIndicator) {
      if (isActive) {
        this.ui.voiceIndicator.classList.add('active');
        this.ui.voiceIndicator.style.width = `${Math.min(level * 200, 100)}%`;
      } else {
        this.ui.voiceIndicator.classList.remove('active');
        this.ui.voiceIndicator.style.width = '0%';
      }
    }

    // Update participant speaking indicators
    this.participants.forEach((participant, participantId) => {
      const levelElement = participant.element.querySelector('.voice-level');
      const speakingIndicator = participant.element.querySelector('.speaking-indicator');

      if (levelElement) {
        // This would need to be implemented with per-participant levels
        levelElement.style.width = '0%';
      }

      if (speakingIndicator) {
        // This would need participant-specific activity data
        speakingIndicator.classList.add('hidden');
      }
    });
  }

  /**
   * Handle speech transcription
   */
  handleTranscription(data) {
    console.log('Transcription:', data.text);

    // Display transcription in chat or log
    this.addTranscriptToChat(data);

    // Check for voice commands
    this.processVoiceCommand(data.text);
  }

  /**
   * Add transcription to chat UI
   */
  addTranscriptToChat(data) {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = 'chat-message transcript';
    messageDiv.innerHTML = `
      <span class="transcript-speaker">${data.participantId || 'You'}</span>
      <span class="transcript-text">${data.text}</span>
      <span class="transcript-confidence">${Math.round(data.confidence * 100)}%</span>
    `;

    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  /**
   * Process voice commands
   */
  processVoiceCommand(text) {
    const commands = {
      'roll dice': () => this.rollDice(),
      'roll initiative': () => this.rollInitiative(),
      'end turn': () => this.endTurn(),
      'cast spell': () => this.openSpellDialog(),
      'use action': () => this.openActionDialog(),
      'status': () => this.reportStatus()
    };

    const lowerText = text.toLowerCase();
    for (const [command, handler] of Object.entries(commands)) {
      if (lowerText.includes(command)) {
        handler();
        break;
      }
    }
  }

  /**
   * Voice command handlers
   */
  rollDice() {
    // Open dice roller dialog
    this.showDiceRoller();
    this.voiceChat.mobileAdapter?.triggerHapticFeedback(20);
  }

  rollInitiative() {
    this.gameState.rollInitiative();
    this.showStatus('Initiative rolled', 'info');
  }

  endTurn() {
    this.gameState.endTurn();
    this.showStatus('Turn ended', 'info');
  }

  openSpellDialog() {
    this.showSpellDialog();
  }

  openActionDialog() {
    this.showActionDialog();
  }

  reportStatus() {
    const status = this.gameState.getMyStatus();
    this.showStatus(`HP: ${status.hp}/${status.maxHp}, AC: ${status.ac}`, 'info');
  }

  /**
   * Handle combat started
   */
  handleCombatStarted(combat) {
    console.log('Combat started:', combat);

    // Update UI for combat mode
    document.body.classList.add('combat-mode');

    // Start combat ambience
    this.voiceChat.gameIntegrator.combatSoundEffects.startCombat(combat.participants);

    // Set combat music intensity
    this.voiceChat.gameIntegrator.setMusicIntensity(0.8);

    this.showStatus('Combat Started!', 'combat');
  }

  /**
   * Handle combat ended
   */
  handleCombatEnded() {
    console.log('Combat ended');

    // Remove combat mode UI
    document.body.classList.remove('combat-mode');

    // Stop combat sounds
    this.voiceChat.gameIntegrator.combatSoundEffects.stopCombat();

    // Restore normal music
    this.voiceChat.gameIntegrator.setMusicIntensity(0.5);

    this.showStatus('Combat Ended', 'info');
  }

  /**
   * Handle spell cast from game
   */
  handleGameSpellCast(spellData) {
    this.voiceChat.gameIntegrator.addSpellAudio(
      spellData.spell,
      spellData.caster,
      spellData.target
    );
  }

  /**
   * Handle spell cast from voice chat
   */
  handleSpellCast(data) {
    // Update game state with spell casting
    this.gameState.castSpell(data.spellName, {
      caster: data.caster,
      target: data.target
    });
  }

  /**
   * Handle environment change
   */
  handleEnvironmentChange(environment) {
    console.log('Environment changed:', environment);

    // Update ambient sounds
    if (environment.type) {
      this.voiceChat.gameIntegrator.ambientSoundManager.setLocation(environment.type);
    }

    // Update weather
    if (environment.weather) {
      this.voiceChat.gameIntegrator.ambientSoundManager.setWeather(environment.weather);
    }

    // Update time of day
    if (environment.timeOfDay) {
      this.voiceChat.gameIntegrator.ambientSoundManager.setTimeOfDay(environment.timeOfDay);
    }
  }

  /**
   * Start talking (push-to-talk)
   */
  startTalking() {
    if (this.voiceChat) {
      this.voiceChat.startRecording();
      this.ui.pushToTalkBtn?.classList.add('active');
    }
  }

  /**
   * Stop talking
   */
  stopTalking() {
    if (this.voiceChat) {
      this.voiceChat.stopRecording();
      this.ui.pushToTalkBtn?.classList.remove('active');
    }
  }

  /**
   * Toggle mute
   */
  toggleMute() {
    if (!this.voiceChat) return;

    const isMuted = this.voiceChat.voiceProcessor.isLocalAudioMuted();
    if (isMuted) {
      this.voiceChat.voiceProcessor.unmute();
      this.ui.muteBtn?.classList.remove('muted');
      this.ui.muteBtn.innerHTML = '🎤';
    } else {
      this.voiceChat.voiceProcessor.mute();
      this.ui.muteBtn?.classList.add('muted');
      this.ui.muteBtn.innerHTML = '🔇';
    }
  }

  /**
   * Set character voice
   */
  setCharacterVoice(characterType) {
    if (this.voiceChat) {
      this.voiceChat.voiceProcessor.setCharacterVoice(characterType);
    }
  }

  /**
   * Update participant position
   */
  updateParticipantPosition(participantId, position) {
    // This would typically come from game state updates
    if (this.voiceChat) {
      this.voiceChat.updateParticipantPosition(participantId, position);
    }
  }

  /**
   * Show status message
   */
  showStatus(message, type = 'info') {
    const statusElement = document.getElementById('status-message');
    if (statusElement) {
      statusElement.textContent = message;
      statusElement.className = `status-message ${type}`;
      statusElement.style.display = 'block';

      setTimeout(() => {
        statusElement.style.display = 'none';
      }, 3000);
    }
  }

  /**
   * Show error message
   */
  showError(message) {
    this.showStatus(message, 'error');
    console.error(message);
  }

  /**
   * Show dice roller
   */
  showDiceRoller() {
    // Implementation would show dice roller UI
    this.showStatus('Dice roller opened', 'info');
  }

  /**
   * Show spell dialog
   */
  showSpellDialog() {
    // Implementation would show spell selection UI
    this.showStatus('Spell dialog opened', 'info');
  }

  /**
   * Show action dialog
   */
  showActionDialog() {
    // Implementation would show action selection UI
    this.showStatus('Action dialog opened', 'info');
  }

  /**
   * Get performance metrics
   */
  getPerformanceMetrics() {
    if (!this.voiceChat) return null;

    return {
      voiceChat: this.voiceChat.getPerformanceMetrics(),
      spatialAudio: this.voiceChat.spatialAudioEngine.getMetrics(),
      voiceProcessor: this.voiceChat.voiceProcessor.getMetrics(),
      gameIntegration: this.voiceChat.gameIntegrator.getMetrics()
    };
  }

  /**
   * Cleanup resources
   */
  async cleanup() {
    if (this.voiceChat) {
      await this.voiceChat.destroy();
      this.voiceChat = null;
    }

    this.participants.clear();

    // Clean up UI
    if (this.ui.participantList) {
      this.ui.participantList.innerHTML = '';
    }
  }
}

// Example usage:
//
// const gameState = new DNDGameState(); // Your game state management
// const voiceIntegration = new DNDVoiceIntegration(gameState);
//
// await voiceIntegration.initialize('dungeon-session-42', {
//   url: 'wss://voice.dmslogn8n.com',
//   token: 'your-auth-token'
// });

export { DNDVoiceIntegration };