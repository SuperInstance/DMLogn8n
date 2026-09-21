import { WebSocket } from 'ws';
import { EventEmitter } from 'events';
import { logger } from '@/utils/logger';

interface OBSScene {
  name: string;
  sources: OBSSource[];
}

interface OBSSource {
  name: string;
  type: string;
  settings: any;
  visible: boolean;
}

interface OBSRequest {
  'request-type': string;
  'message-id': string;
  [key: string]: any;
}

interface OBSResponse {
  'message-id': string;
  status: string;
  error?: string;
  [key: string]: any;
}

export class OBSController extends EventEmitter {
  private static instance: OBSController;
  private ws: WebSocket | null = null;
  private isConnected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;
  private url: string;
  private password: string;
  private messageIdCounter = 0;
  private pendingRequests: Map<string, (response: OBSResponse) => void> = new Map();
  private scenes: Map<string, OBSScene> = new Map();
  private currentScene = '';

  private constructor() {
    super();
    this.url = process.env.OBS_WEBSOCKET_URL || 'ws://localhost:4444';
    this.password = process.env.OBS_WEBSOCKET_PASSWORD || '';
  }

  public static getInstance(): OBSController {
    if (!OBSController.instance) {
      OBSController.instance = new OBSController();
    }
    return OBSController.instance;
  }

  public static async initialize(): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.connect();
  }

  public static isConnected(): boolean {
    return OBSController.getInstance().isConnected;
  }

  private async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.url);

        this.ws.on('open', () => {
          logger.info('Connected to OBS WebSocket');
          this.isConnected = true;
          this.reconnectAttempts = 0;

          // Authenticate if password is provided
          if (this.password) {
            this.authenticate(this.password)
              .then(() => {
                this.loadScenes()
                  .then(() => resolve())
                  .catch(reject);
              })
              .catch(reject);
          } else {
            this.loadScenes()
              .then(() => resolve())
              .catch(reject);
          }
        });

        this.ws.on('message', (data: Buffer) => {
          this.handleMessage(data.toString());
        });

        this.ws.on('close', () => {
          this.isConnected = false;
          this.ws = null;
          logger.warn('OBS WebSocket connection closed');
          this.attemptReconnect();
        });

        this.ws.on('error', (error) => {
          logger.error('OBS WebSocket error:', error);
          this.isConnected = false;
          reject(error);
        });

      } catch (error) {
        logger.error('Failed to connect to OBS:', error);
        reject(error);
      }
    });
  }

  private handleMessage(data: string): void {
    try {
      const lines = data.trim().split('\n');
      for (const line of lines) {
        if (!line.trim()) continue;

        let message: any;
        try {
          message = JSON.parse(line);
        } catch (e) {
          continue; // Skip invalid JSON
        }

        // Handle response to specific request
        if (message['message-id']) {
          const callback = this.pendingRequests.get(message['message-id']);
          if (callback) {
            callback(message);
            this.pendingRequests.delete(message['message-id']);
          }
        }

        // Handle events
        if (message['update-type']) {
          this.handleEvent(message);
        }
      }
    } catch (error) {
      logger.error('Error parsing OBS WebSocket message:', error);
    }
  }

  private handleEvent(event: any): void {
    switch (event['update-type']) {
      case 'StreamStarted':
        this.emit('streamStarted', event);
        break;
      case 'StreamStopped':
        this.emit('streamStopped', event);
        break;
      case 'RecordingStarted':
        this.emit('recordingStarted', event);
        break;
      case 'RecordingStopped':
        this.emit('recordingStopped', event);
        break;
      case 'SceneChanged':
        this.currentScene = event['scene-name'];
        this.emit('sceneChanged', event);
        break;
      case 'SwitchScenes':
        this.currentScene = event['scene-name'];
        this.emit('sceneChanged', event);
        break;
      case 'SourceChanged':
        this.emit('sourceChanged', event);
        break;
      default:
        this.emit('obsEvent', event);
    }
  }

  private async authenticate(password: string): Promise<void> {
    const response = await this.sendRequest({
      'request-type': 'GetAuthRequired'
    });

    if (response.authRequired) {
      const authResponse = await this.sendRequest({
        'request-type': 'Authenticate',
        'auth': this.generateAuth(password, response.salt, response.challenge)
      });

      if (authResponse.status !== 'ok') {
        throw new Error('OBS authentication failed');
      }
    }

    logger.info('OBS authentication successful');
  }

  private generateAuth(password: string, salt: string, challenge: string): string {
    const crypto = require('crypto');
    const hash = crypto.createHash('sha256');
    hash.update(password + salt);
    const authHash = hash.digest('base64');

    const authResponseHash = crypto.createHash('sha256');
    authResponseHash.update(authHash + challenge);
    return authResponseHash.digest('base64');
  }

  private async sendRequest(request: Partial<OBSRequest>): Promise<OBSResponse> {
    return new Promise((resolve, reject) => {
      if (!this.ws || !this.isConnected) {
        reject(new Error('OBS WebSocket not connected'));
        return;
      }

      const messageId = this.getNextMessageId();
      const fullRequest: OBSRequest = {
        'request-type': request['request-type']!,
        'message-id': messageId,
        ...request
      };

      this.pendingRequests.set(messageId, (response: OBSResponse) => {
        if (response.status === 'error') {
          reject(new Error(response.error || 'OBS request failed'));
        } else {
          resolve(response);
        }
      });

      this.ws!.send(JSON.stringify(fullRequest));

      // Timeout after 10 seconds
      setTimeout(() => {
        if (this.pendingRequests.has(messageId)) {
          this.pendingRequests.delete(messageId);
          reject(new Error('OBS request timeout'));
        }
      }, 10000);
    });
  }

  private getNextMessageId(): string {
    return `msg_${++this.messageIdCounter}_${Date.now()}`;
  }

  private async attemptReconnect(): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      logger.error('Max OBS reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    logger.info(`Attempting OBS reconnection (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(async () => {
      try {
        await this.connect();
      } catch (error) {
        logger.error('OBS reconnection failed:', error);
      }
    }, this.reconnectInterval);
  }

  private async loadScenes(): Promise<void> {
    const response = await this.sendRequest({
      'request-type': 'GetSceneList'
    });

    this.scenes.clear();
    for (const scene of response.scenes) {
      const sceneDetails = await this.getSceneDetails(scene.name);
      this.scenes.set(scene.name, {
        name: scene.name,
        sources: sceneDetails.sources
      });
    }

    this.currentScene = response['current-scene'];
    logger.info(`Loaded ${this.scenes.size} OBS scenes`);
  }

  private async getSceneDetails(sceneName: string): Promise<any> {
    return await this.sendRequest({
      'request-type': 'GetSceneItemList',
      'scene-name': sceneName
    });
  }

  // Public API methods

  public static async switchScene(sceneName: string): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'SetCurrentScene',
      'scene-name': sceneName
    });
    logger.info(`Switched to OBS scene: ${sceneName}`);
  }

  public static async getCurrentScene(): Promise<string> {
    const controller = OBSController.getInstance();
    const response = await controller.sendRequest({
      'request-type': 'GetCurrentScene'
    });
    return response['name'];
  }

  public static async getScenes(): Promise<string[]> {
    const controller = OBSController.getInstance();
    return Array.from(controller.scenes.keys());
  }

  public static async createScene(sceneName: string): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'AddScene',
      'sceneName': sceneName
    });
    await controller.loadScenes();
  }

  public static async startStreaming(): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'StartStreaming'
    });
    logger.info('OBS streaming started');
  }

  public static async stopStreaming(): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'StopStreaming'
    });
    logger.info('OBS streaming stopped');
  }

  public static async startRecording(): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'StartRecording'
    });
    logger.info('OBS recording started');
  }

  public static async stopRecording(): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'StopRecording'
    });
    logger.info('OBS recording stopped');
  }

  public static async getSourceSettings(sourceName: string): Promise<any> {
    const controller = OBSController.getInstance();
    return await controller.sendRequest({
      'request-type': 'GetSourceSettings',
      'sourceName': sourceName
    });
  }

  public static async setSourceSettings(sourceName: string, sourceType: string, settings: any): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'SetSourceSettings',
      'sourceName': sourceName,
      'sourceType': sourceType,
      'sourceSettings': settings
    });
  }

  public static async setSourceVisibility(sourceName: string, visible: boolean): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'SetSceneItemProperties',
      'scene-name': controller.currentScene,
      'item': sourceName,
      'visible': visible
    });
  }

  public static async setBrowserSourceURL(sourceName: string, url: string): Promise<void> {
    await OBSController.setSourceSettings(sourceName, 'browser_source', {
      url: url
    });
  }

  public static async setTextSourceText(sourceName: string, text: string): Promise<void> {
    await OBSController.setSourceSettings(sourceName, 'text_gdiplus', {
      text: text
    });
  }

  public static async setImageSourceFile(sourceName: string, file: string): Promise<void> {
    await OBSController.setSourceSettings(sourceName, 'image_source', {
      file: file
    });
  }

  public static async createBrowserSource(name: string, url: string, width: number = 1920, height: number = 1080): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'AddSceneItem',
      'sceneName': controller.currentScene,
      'sourceName': name,
      'sourceSettings': {
        url: url,
        width: width,
        height: height,
        css: '' // Custom CSS if needed
      }
    });
  }

  public static async createTextSource(name: string, text: string, fontSize: number = 72): Promise<void> {
    const controller = OBSController.getInstance();
    await controller.sendRequest({
      'request-type': 'AddSceneItem',
      'sceneName': controller.currentScene,
      'sourceName': name,
      'sourceSettings': {
        text: text,
        font: {
          face: 'Arial',
          size: fontSize,
          style: 'Regular'
        },
        color: 0xFFFFFFFF,
        background_color: 0x00000000,
        outline: false,
        outline_color: 0x000000FF,
        outline_size: 2,
        drop_shadow: false,
        gradient: false,
        gradient_color: 0x000000FF,
        gradient_dir: 90.0,
        gradient_opacity: 50
      }
    });
  }

  public static async takeScreenshot(): Promise<string> {
    const controller = OBSController.getInstance();
    const response = await controller.sendRequest({
      'request-type': 'TakeSourceScreenshot',
      'sourceName': '',
      'embedPictureFormat': 'png',
      'saveToFilePath': './obs-screenshot.png'
    });
    return response.imageData || '';
  }

  public static async getStreamStatus(): Promise<any> {
    const controller = OBSController.getInstance();
    return await controller.sendRequest({
      'request-type': 'GetStreamingStatus'
    });
  }

  public static async getRecordingStatus(): Promise<any> {
    const controller = OBSController.getInstance();
    return await controller.sendRequest({
      'request-type': 'GetRecordingStatus'
    });
  }

  public static disconnect(): void {
    const controller = OBSController.getInstance();
    if (controller.ws) {
      controller.ws.close();
      controller.ws = null;
    }
    controller.isConnected = false;
  }
}

export default OBSController;