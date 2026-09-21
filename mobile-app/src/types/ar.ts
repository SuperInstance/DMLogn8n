export interface ARMarker {
  id: string;
  name: string;
  type: 'miniature' | 'prop' | 'effect' | 'terrain';
  model: string;
  position: {
    x: number;
    y: number;
    z: number;
  };
  rotation: {
    x: number;
    y: number;
    z: number;
  };
  scale: number;
  size: {
    width: number;
    height: number;
    depth: number;
  };
  animation?: string;
  image?: string;
  customData?: Record<string, any>;
}

export interface ARModel {
  id: string;
  name: string;
  type: 'miniature' | 'prop' | 'effect' | 'terrain';
  modelUrl: string;
  textureUrl?: string;
  scale: number;
  animations: string[];
  effects: string[];
  category: string;
  rarity: 'common' | 'uncommon' | 'rare' | 'legendary';
  customProperties?: Record<string, any>;
}

export interface ARScene {
  id: string;
  name: string;
  campaignId?: string;
  markers: ARMarker[];
  background?: string;
  lighting?: {
    ambientLight: number;
    directionalLight: {
      intensity: number;
      direction: { x: number; y: number; z: number };
      color: string;
    };
  };
  environment?: {
    skybox?: string;
    fog?: {
      enabled: boolean;
      density: number;
      color: string;
    };
  };
  createdAt: string;
  updatedAt: string;
  isPublic: boolean;
  shareCode?: string;
  thumbnail?: string;
}

export interface ARDetectionResult {
  marker: ARMarker;
  confidence: number;
  boundingBox: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
  keypoints?: {
    x: number;
    y: number;
  }[];
}

export interface ARRenderSettings {
  quality: 'low' | 'medium' | 'high' | 'ultra';
  shadows: boolean;
  antialiasing: boolean;
  postProcessing: boolean;
  frameRate: number;
  maxDistance: number;
}

export interface AREnvironmentSettings {
  lighting: 'day' | 'night' | 'dungeon' | 'custom';
  weather: 'clear' | 'rain' | 'fog' | 'snow' | 'custom';
  timeOfDay: 'dawn' | 'morning' | 'noon' | 'afternoon' | 'dusk' | 'night';
  effects: string[];
}

export interface ARInteractionEvent {
  type: 'tap' | 'long_press' | 'drag' | 'pinch' | 'rotate';
  position: { x: number; y: number };
  target?: ARMarker;
  timestamp: number;
  gestureData?: {
    distance?: number;
    rotation?: number;
    velocity?: { x: number; y: number };
  };
}

export interface ARSessionSettings {
  maxMarkers: number;
  trackingMode: 'world' | 'face' | 'image';
  planeDetection: boolean;
  lightEstimation: boolean;
  occlusion: boolean;
  collaboration: boolean;
}

export interface ARShareSettings {
  allowPublicView: boolean;
  allowEdit: boolean;
  allowDuplicate: boolean;
  expiresAt?: string;
  password?: string;
  maxParticipants?: number;
}

export interface ARPerformanceMetrics {
  frameRate: number;
  renderTime: number;
  markerCount: number;
  trackingQuality: number;
  memoryUsage: number;
  batteryDrain: number;
  thermalState: 'normal' | 'warm' | 'hot' | 'critical';
}