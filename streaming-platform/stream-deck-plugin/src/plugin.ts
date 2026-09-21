import { StreamDeck } from '@elgato/streamdeck';
import { WebSocket } from 'ws';
import axios from 'axios';

interface PluginSettings {
  serverUrl: string;
  apiKey: string;
  obsUrl: string;
  obsPassword: string;
  autoConnect: boolean;
}

interface ActionSettings {
  sceneName?: string;
  diceNotation?: string;
  characterName?: string;
  pollQuestion?: string;
  pollOptions?: string[];
  chatMessage?: string;
  soundFile?: string;
  lowerThirdText?: string;
}

export class DnDStreamingPlugin extends StreamDeck<PluginSettings> {
  private serverWs: WebSocket | null = null;
  private obsWs: WebSocket | null = null;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  constructor() {
    super();

    // Connect to main streaming platform server
    this.connectToServer();
  }

  private async connectToServer(): Promise<void> {
    try {
      const settings = await this.getSettings();

      if (!settings.serverUrl) {
        this.logMessage('Server URL not configured');
        return;
      }

      this.serverWs = new WebSocket(settings.serverUrl);

      this.serverWs.on('open', () => {
        this.logMessage('Connected to streaming server');
        this.isConnected = true;
        this.reconnectAttempts = 0;

        // Authenticate
        if (settings.apiKey) {
          this.sendToServer({
            type: 'streamdeck-connect',
            apiKey: settings.apiKey,
            version: '1.0.0'
          });
        }
      });

      this.serverWs.on('message', (data) => {
        try {
          const message = JSON.parse(data.toString());
          this.handleServerMessage(message);
        } catch (error) {
          this.logMessage(`Failed to parse server message: ${error}`);
        }
      });

      this.serverWs.on('close', () => {
        this.logMessage('Disconnected from streaming server');
        this.isConnected = false;
        this.attemptReconnect();
      });

      this.serverWs.on('error', (error) => {
        this.logMessage(`Server connection error: ${error}`);
      });

    } catch (error) {
      this.logMessage(`Failed to connect to server: ${error}`);
    }
  }

  private handleServerMessage(message: any): void {
    switch (message.type) {
      case 'stream-status':
        this.updateStreamStatus(message.data);
        break;
      case 'scene-changed':
        this.updateSceneStatus(message.data);
        break;
      case 'viewer-count':
        this.updateViewerCount(message.data);
        break;
      case 'donation-received':
        this.showDonationAlert(message.data);
        break;
    }
  }

  private sendToServer(message: any): void {
    if (this.serverWs && this.isConnected) {
      this.serverWs.send(JSON.stringify(message));
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      this.logMessage('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    setTimeout(() => {
      this.logMessage(`Attempting reconnection (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connectToServer();
    }, 5000);
  }

  // Action handlers

  protected async OnDidReceiveSettings(
    action: string,
    context: string,
    settings: ActionSettings
  ): Promise<void> {
    // Update action when settings change
    this.updateActionState(action, context, settings);
  }

  // Start Stream Action
  protected async OnKeyDown(
    action: string,
    context: string,
    { payload }: { payload: { settings: ActionSettings } }
  ): Promise<void> {
    if (action === 'com.dndstreaming.streamdeck.startstream') {
      this.startStream(context);
    } else if (action === 'com.dndstreaming.streamdeck.stopstream') {
      this.stopStream(context);
    } else if (action === 'com.dndstreaming.streamdeck.sceneswitcher') {
      this.switchScene(context, payload.settings);
    } else if (action === 'com.dndstreaming.streamdeck.diceroller') {
      this.rollDice(context, payload.settings);
    } else if (action === 'com.dndstreaming.streamdeck.characterdisplay') {
      this.toggleCharacterDisplay(context, payload.settings);
    } else if (action === 'com.dndstreaming.streamdeck.quickpoll') {
      this.createQuickPoll(context, payload.settings);
    } else if (action === 'com.dndstreaming.streamdeck.donationalert') {
      this.triggerDonationAlert(context);
    } else if (action === 'com.dndstreaming.streamdeck.highlightmarker') {
      this.markHighlight(context);
    } else if (action === 'com.dndstreaming.streamdeck.chatcommand') {
      this.sendChatCommand(context, payload.settings);
    } else if (action === 'com.dndstreaming.streamdeck.soundboard') {
      this.playSound(context, payload.settings);
    } else if (action === 'com.dndstreaming.streamdeck.lowerthird') {
      this.showLowerThird(context, payload.settings);
    }
  }

  private async startStream(context: string): Promise<void> {
    try {
      this.sendToServer({
        type: 'start-stream',
        platforms: ['twitch', 'youtube', 'facebook']
      });

      // Show feedback
      this.setImage(context, 'images/actions/streaming.png');
      this.setTitle(context, 'STARTING...');

      // Auto-revert after 3 seconds
      setTimeout(() => {
        this.setImage(context, 'images/actions/startstream.png');
        this.setTitle(context, '');
      }, 3000);

    } catch (error) {
      this.logMessage(`Failed to start stream: ${error}`);
      this.showAlert(context);
    }
  }

  private async stopStream(context: string): Promise<void> {
    try {
      this.sendToServer({
        type: 'stop-stream'
      });

      // Show feedback
      this.setImage(context, 'images/actions/stopping.png');
      this.setTitle(context, 'STOPPING...');

      // Auto-revert after 3 seconds
      setTimeout(() => {
        this.setImage(context, 'images/actions/stopstream.png');
        this.setTitle(context, '');
      }, 3000);

    } catch (error) {
      this.logMessage(`Failed to stop stream: ${error}`);
      this.showAlert(context);
    }
  }

  private async switchScene(context: string, settings: ActionSettings): Promise<void> {
    if (!settings.sceneName) {
      this.showAlert(context);
      return;
    }

    try {
      this.sendToServer({
        type: 'switch-scene',
        sceneName: settings.sceneName
      });

      // Show feedback
      this.setTitle(context, settings.sceneName.toUpperCase());

    } catch (error) {
      this.logMessage(`Failed to switch scene: ${error}`);
      this.showAlert(context);
    }
  }

  private async rollDice(context: string, settings: ActionSettings): Promise<void> {
    const diceNotation = settings.diceNotation || '1d20';

    try {
      this.sendToServer({
        type: 'roll-dice',
        notation: diceNotation,
        playerName: 'Stream Deck'
      });

      // Show animated feedback
      this.setImage(context, 'images/actions/dicerolling.gif');
      this.setTitle(context, diceNotation);

      // Revert after animation
      setTimeout(() => {
        this.setImage(context, 'images/actions/dice.png');
        this.setTitle(context, '');
      }, 2000);

    } catch (error) {
      this.logMessage(`Failed to roll dice: ${error}`);
      this.showAlert(context);
    }
  }

  private async toggleCharacterDisplay(context: string, settings: ActionSettings): Promise<void> {
    try {
      this.sendToServer({
        type: 'toggle-character',
        characterName: settings.characterName || 'Current Character'
      });

      // Toggle state
      const currentState = await this.getState(context);
      const newState = !currentState?.showing;
      await this.setState(context, { showing: newState });

      this.setImage(context, newState ? 'images/actions/character-on.png' : 'images/actions/character.png');

    } catch (error) {
      this.logMessage(`Failed to toggle character display: ${error}`);
      this.showAlert(context);
    }
  }

  private async createQuickPoll(context: string, settings: ActionSettings): Promise<void> {
    if (!settings.pollQuestion || !settings.pollOptions || settings.pollOptions.length < 2) {
      this.showAlert(context);
      return;
    }

    try {
      this.sendToServer({
        type: 'create-poll',
        question: settings.pollQuestion,
        options: settings.pollOptions,
        duration: 60 // 60 seconds
      });

      // Show feedback
      this.setImage(context, 'images/actions/pollactive.png');
      this.setTitle(context, 'POLL ACTIVE');

      // Revert after duration
      setTimeout(() => {
        this.setImage(context, 'images/actions/poll.png');
        this.setTitle(context, '');
      }, 60000);

    } catch (error) {
      this.logMessage(`Failed to create poll: ${error}`);
      this.showAlert(context);
    }
  }

  private async triggerDonationAlert(context: string): Promise<void> {
    try {
      this.sendToServer({
        type: 'trigger-donation-alert',
        amount: 100,
        donorName: 'Test Donation',
        message: 'Stream Deck test donation!'
      });

      // Show feedback
      this.setImage(context, 'images/actions/donationactive.gif');

      setTimeout(() => {
        this.setImage(context, 'images/actions/donation.png');
      }, 3000);

    } catch (error) {
      this.logMessage(`Failed to trigger donation alert: ${error}`);
      this.showAlert(context);
    }
  }

  private async markHighlight(context: string): Promise<void> {
    try {
      this.sendToServer({
        type: 'mark-highlight',
        timestamp: Date.now(),
        type: 'manual'
      });

      // Show feedback
      this.setImage(context, 'images/actions/highlightmarked.png');
      this.setTitle(context, 'MARKED');

      setTimeout(() => {
        this.setImage(context, 'images/actions/highlight.png');
        this.setTitle(context, '');
      }, 2000);

    } catch (error) {
      this.logMessage(`Failed to mark highlight: ${error}`);
      this.showAlert(context);
    }
  }

  private async sendChatCommand(context: string, settings: ActionSettings): Promise<void> {
    if (!settings.chatMessage) {
      this.showAlert(context);
      return;
    }

    try {
      this.sendToServer({
        type: 'send-chat-message',
        message: settings.chatMessage,
        platform: 'all'
      });

      // Show feedback
      this.setImage(context, 'images/actions/chatsent.png');
      this.setTitle(context, 'SENT');

      setTimeout(() => {
        this.setImage(context, 'images/actions/chat.png');
        this.setTitle(context, '');
      }, 2000);

    } catch (error) {
      this.logMessage(`Failed to send chat command: ${error}`);
      this.showAlert(context);
    }
  }

  private async playSound(context: string, settings: ActionSettings): Promise<void> {
    if (!settings.soundFile) {
      this.showAlert(context);
      return;
    }

    try {
      this.sendToServer({
        type: 'play-sound',
        soundFile: settings.soundFile
      });

      // Show feedback
      this.setImage(context, 'images/actions/soundplaying.gif');

      setTimeout(() => {
        this.setImage(context, 'images/actions/sound.png');
      }, 1000);

    } catch (error) {
      this.logMessage(`Failed to play sound: ${error}`);
      this.showAlert(context);
    }
  }

  private async showLowerThird(context: string, settings: ActionSettings): Promise<void> {
    const text = settings.lowerThirdText || 'D&D Streaming';

    try {
      this.sendToServer({
        type: 'show-lower-third',
        text: text,
        duration: 5000
      });

      // Show feedback
      this.setImage(context, 'images/actions/lowerthirdactive.png');

      setTimeout(() => {
        this.setImage(context, 'images/actions/lowerthird.png');
      }, 5000);

    } catch (error) {
      this.logMessage(`Failed to show lower third: ${error}`);
      this.showAlert(context);
    }
  }

  // Status updates
  private updateStreamStatus(status: any): void {
    // Update stream status displays
    this.updateAllActions('com.dndstreaming.streamdeck.streamstatus', (context) => {
      this.setTitle(context, status.isLive ? 'LIVE' : 'OFFLINE');
      this.setImage(context, status.isLive ? 'images/actions/live.png' : 'images/actions/offline.png');
    });
  }

  private updateSceneStatus(data: any): void {
    // Update scene switcher displays
    this.updateAllActions('com.dndstreaming.streamdeck.sceneswitcher', async (context) => {
      const settings = await this.getSettings(context);
      if (settings.sceneName === data.sceneName) {
        this.setImage(context, 'images/actions/sceneactive.png');
      } else {
        this.setImage(context, 'images/actions/scenes.png');
      }
    });
  }

  private updateViewerCount(data: any): void {
    // Update stream status with viewer count
    this.updateAllActions('com.dndstreaming.streamdeck.streamstatus', (context) => {
      this.setTitle(context, `VIEWERS: ${data.count}`);
    });
  }

  private showDonationAlert(data: any): void {
    // Flash donation alert buttons
    this.updateAllActions('com.dndstreaming.streamdeck.donationalert', (context) => {
      this.setImage(context, 'images/actions/donationalert.gif');
      this.setTitle(context, `$${data.amount}`);

      setTimeout(() => {
        this.setImage(context, 'images/actions/donation.png');
        this.setTitle(context, '');
      }, 5000);
    });
  }

  private async updateActionState(action: string, context: string, settings: ActionSettings): Promise<void> {
    // Update action appearance based on settings
    if (action === 'com.dndstreaming.streamdeck.diceroller' && settings.diceNotation) {
      this.setTitle(context, settings.diceNotation);
    } else if (action === 'com.dndstreaming.streamdeck.sceneswitcher' && settings.sceneName) {
      this.setTitle(context, settings.sceneName.toUpperCase());
    } else if (action === 'com.dndstreaming.streamdeck.chatcommand' && settings.chatMessage) {
      this.setTitle(context, settings.chatMessage.substring(0, 15) + (settings.chatMessage.length > 15 ? '...' : ''));
    }
  }

  private updateAllActions(actionType: string, callback: (context: string) => void): void {
    // This would need to track all active instances and update them
    // Implementation depends on StreamDeck API specifics
  }

  // Utility methods
  private async updateAction(context: string, updates: Partial<ActionSettings>): Promise<void> {
    const current = await this.getSettings(context);
    await this.setSettings(context, { ...current, ...updates });
  }

  protected async OnWillAppear(
    action: string,
    context: string,
    { payload }: { payload: { settings: ActionSettings } }
  ): Promise<void> {
    // Initialize action appearance
    this.updateActionState(action, context, payload.settings);
  }
}

// Plugin initialization
const plugin = new DnDStreamingPlugin();
plugin.connect();