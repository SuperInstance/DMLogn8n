import { ARMarker, ARDetectionResult, ARModel, ARScene } from '../types/ar';

export class ARService {
  private static instance: ARService;
  private isInitialized: boolean = false;
  private availableModels: Map<string, ARModel> = new Map();
  private activeScene: ARScene | null = null;

  private constructor() {}

  static getInstance(): ARService {
    if (!ARService.instance) {
      ARService.instance = new ARService();
    }
    return ARService.instance;
  }

  async initialize(): Promise<void> {
    try {
      // Load AR models and configurations
      await this.loadARModels();
      this.isInitialized = true;
      console.log('AR service initialized');
    } catch (error) {
      console.error('Failed to initialize AR service:', error);
    }
  }

  private async loadARModels(): Promise<void> {
    try {
      // Load built-in AR models
      const models: ARModel[] = [
        {
          id: 'dragon',
          name: 'Ancient Dragon',
          type: 'miniature',
          modelUrl: 'assets/ar/models/dragon.glb',
          textureUrl: 'assets/ar/textures/dragon.png',
          scale: 1.0,
          animations: ['idle', 'attack', 'fly'],
          effects: ['fire_breath', 'wing_flap'],
          category: 'monster',
          rarity: 'legendary',
        },
        {
          id: 'knight',
          name: 'Human Knight',
          type: 'miniature',
          modelUrl: 'assets/ar/models/knight.glb',
          textureUrl: 'assets/ar/textures/knight.png',
          scale: 0.8,
          animations: ['idle', 'walk', 'attack', 'defend'],
          effects: ['sword_glow', 'shield_block'],
          category: 'character',
          rarity: 'common',
        },
        {
          id: 'chest',
          name: 'Treasure Chest',
          type: 'prop',
          modelUrl: 'assets/ar/models/chest.glb',
          textureUrl: 'assets/ar/textures/chest.png',
          scale: 1.0,
          animations: ['closed', 'opening', 'open'],
          effects: ['gold_sparkle', 'magic_glow'],
          category: 'prop',
          rarity: 'uncommon',
        },
        {
          id: 'spell_fireball',
          name: 'Fireball',
          type: 'effect',
          modelUrl: 'assets/ar/models/fireball.glb',
          textureUrl: 'assets/ar/textures/fireball.png',
          scale: 0.5,
          animations: ['launch', 'explode'],
          effects: ['fire_trail', 'explosion'],
          category: 'spell',
          rarity: 'common',
        },
      ];

      models.forEach(model => {
        this.availableModels.set(model.id, model);
      });

      console.log(`Loaded ${models.length} AR models`);
    } catch (error) {
      console.error('Failed to load AR models:', error);
    }
  }

  async detectARMarkers(imageData: string): Promise<ARDetectionResult[]> {
    try {
      // Simulate AR marker detection
      // In a real implementation, this would use computer vision libraries
      const mockDetections: ARDetectionResult[] = [
        {
          marker: {
            id: 'marker_001',
            name: 'Dragon Miniature',
            type: 'miniature',
            model: 'dragon',
            position: { x: 0.5, y: 0.3, z: 0 },
            rotation: { x: 0, y: 45, z: 0 },
            scale: 1.0,
            size: { width: 50, height: 80, depth: 50 },
          },
          confidence: 0.95,
          boundingBox: {
            x: 100,
            y: 150,
            width: 100,
            height: 160,
          },
        },
      ];

      return mockDetections;
    } catch (error) {
      console.error('Failed to detect AR markers:', error);
      return [];
    }
  }

  async createARMarker(
    type: 'miniature' | 'prop' | 'effect' | 'terrain',
    modelId: string,
    position: { x: number; y: number; z: number },
    options?: {
      scale?: number;
      rotation?: { x: number; y: number; z: number };
      animation?: string;
      effect?: string;
    }
  ): Promise<ARMarker> {
    try {
      const model = this.availableModels.get(modelId);
      if (!model) {
        throw new Error(`Model not found: ${modelId}`);
      }

      const marker: ARMarker = {
        id: `marker_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name: model.name,
        type,
        model: modelId,
        position,
        rotation: options?.rotation || { x: 0, y: 0, z: 0 },
        scale: options?.scale || model.scale,
        size: this.calculateModelSize(model, options?.scale || model.scale),
        animation: options?.animation,
      };

      return marker;
    } catch (error) {
      console.error('Failed to create AR marker:', error);
      throw error;
    }
  }

  private calculateModelSize(model: ARModel, scale: number): { width: number; height: number; depth: number } {
    // Base sizes for different model types
    const baseSizes = {
      miniature: { width: 30, height: 50, depth: 30 },
      prop: { width: 40, height: 30, depth: 40 },
      effect: { width: 20, height: 20, depth: 20 },
      terrain: { width: 100, height: 50, depth: 100 },
    };

    const baseSize = baseSizes[model.type] || baseSizes.miniature;

    return {
      width: baseSize.width * scale,
      height: baseSize.height * scale,
      depth: baseSize.depth * scale,
    };
  }

  async placeMarkerInScene(
    marker: ARMarker,
    sceneId?: string
  ): Promise<string> {
    try {
      if (!this.activeScene && !sceneId) {
        throw new Error('No active scene to place marker in');
      }

      const targetScene = this.activeScene || { id: sceneId!, markers: [], name: 'Untitled Scene' };

      targetScene.markers.push(marker);

      if (!this.activeScene) {
        this.activeScene = targetScene;
      }

      return marker.id;
    } catch (error) {
      console.error('Failed to place marker in scene:', error);
      throw error;
    }
  }

  async createARScene(name: string, campaignId?: string): Promise<ARScene> {
    try {
      const scene: ARScene = {
        id: `scene_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        name,
        campaignId,
        markers: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isPublic: false,
      };

      this.activeScene = scene;

      return scene;
    } catch (error) {
      console.error('Failed to create AR scene:', error);
      throw error;
    }
  }

  async saveARScene(scene: ARScene): Promise<void> {
    try {
      // Save scene to local storage or backend
      scene.updatedAt = new Date().toISOString();

      if (this.activeScene?.id === scene.id) {
        this.activeScene = scene;
      }

      console.log(`Saved AR scene: ${scene.name}`);
    } catch (error) {
      console.error('Failed to save AR scene:', error);
      throw error;
    }
  }

  async loadARScene(sceneId: string): Promise<ARScene> {
    try {
      // Load scene from storage or backend
      // For now, return a mock scene
      const scene: ARScene = {
        id: sceneId,
        name: 'Battle Scene',
        campaignId: 'campaign_001',
        markers: [
          {
            id: 'marker_001',
            name: 'Dragon',
            type: 'miniature',
            model: 'dragon',
            position: { x: 0.5, y: 0.3, z: 0 },
            rotation: { x: 0, y: 45, z: 0 },
            scale: 1.0,
            size: { width: 50, height: 80, depth: 50 },
          },
        ],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        isPublic: false,
      };

      this.activeScene = scene;

      return scene;
    } catch (error) {
      console.error('Failed to load AR scene:', error);
      throw error;
    }
  }

  async shareARScene(sceneId: string, shareOptions?: {
    isPublic?: boolean;
    allowEdit?: boolean;
    expiresAt?: Date;
  }): Promise<string> {
    try {
      const shareCode = `AR_${sceneId}_${Math.random().toString(36).substr(2, 9)}`;

      // Create shareable link
      const shareUrl = `https://dmlogn8n.com/ar/${shareCode}`;

      console.log(`Shared AR scene: ${shareUrl}`);

      return shareUrl;
    } catch (error) {
      console.error('Failed to share AR scene:', error);
      throw error;
    }
  }

  async loadARSceneFromShareCode(shareCode: string): Promise<ARScene> {
    try {
      const sceneId = shareCode.replace('AR_', '').split('_')[0];
      return await this.loadARScene(sceneId);
    } catch (error) {
      console.error('Failed to load AR scene from share code:', error);
      throw error;
    }
  }

  getAvailableModels(category?: string): ARModel[] {
    const models = Array.from(this.availableModels.values());

    if (category) {
      return models.filter(model => model.category === category);
    }

    return models;
  }

  getModel(modelId: string): ARModel | undefined {
    return this.availableModels.get(modelId);
  }

  getActiveScene(): ARScene | null {
    return this.activeScene;
  }

  setActiveScene(scene: ARScene): void {
    this.activeScene = scene;
  }

  async addCustomModel(model: ARModel): Promise<void> {
    try {
      this.availableModels.set(model.id, model);
      console.log(`Added custom AR model: ${model.name}`);
    } catch (error) {
      console.error('Failed to add custom AR model:', error);
      throw error;
    }
  }

  async removeCustomModel(modelId: string): Promise<void> {
    try {
      this.availableModels.delete(modelId);
      console.log(`Removed AR model: ${modelId}`);
    } catch (error) {
      console.error('Failed to remove AR model:', error);
      throw error;
    }
  }

  async animateMarker(
    markerId: string,
    animation: string,
    duration?: number,
    loop?: boolean
  ): Promise<void> {
    try {
      const model = this.availableModels.get(markerId);
      if (!model || !model.animations.includes(animation)) {
        throw new Error(`Animation ${animation} not available for model ${markerId}`);
      }

      console.log(`Starting animation ${animation} for marker ${markerId}`);
      // In a real implementation, this would trigger the animation
    } catch (error) {
      console.error('Failed to animate marker:', error);
      throw error;
    }
  }

  async triggerMarkerEffect(
    markerId: string,
    effect: string,
    targetPosition?: { x: number; y: number; z: number }
  ): Promise<void> {
    try {
      const model = this.availableModels.get(markerId);
      if (!model || !model.effects.includes(effect)) {
        throw new Error(`Effect ${effect} not available for model ${markerId}`);
      }

      console.log(`Triggering effect ${effect} for marker ${markerId}`);
      // In a real implementation, this would trigger the visual effect
    } catch (error) {
      console.error('Failed to trigger marker effect:', error);
      throw error;
    }
  }

  getIsInitialized(): boolean {
    return this.isInitialized;
  }

  cleanup(): void {
    this.activeScene = null;
    this.availableModels.clear();
    this.isInitialized = false;
  }
}

// AR-related types for the service
export interface ARMeasurementData {
  markerId: string;
  distance: number;
  angle: number;
  relativePosition: {
    x: number;
    y: number;
    z: number;
  };
}

export interface ARCalibrationData {
  cameraIntrinsics: {
    focalLength: { x: number; y: number };
    principalPoint: { x: number; y: number };
  };
  distortionCoefficients: number[];
  arucoDictionary: string;
  markerSize: number;
}

export interface ARTrackingState {
  isTracking: boolean;
  trackingQuality: 'good' | 'poor' | 'lost';
  markersDetected: number;
  lastUpdateTime: number;
}