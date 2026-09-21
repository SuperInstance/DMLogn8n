import * as THREE from 'three'

// Core types for the Visual Combat Effects System

export interface Character {
  id: string
  name: string
  position: THREE.Vector3
  rotation: number
  health: number
  maxHealth: number
  class: CharacterClass
  level: number
  mesh?: THREE.Object3D
  animationState: AnimationState
  statusEffects: StatusEffect[]
}

export enum CharacterClass {
  Fighter = 'fighter',
  Wizard = 'wizard',
  Rogue = 'rogue',
  Cleric = 'cleric',
  Barbarian = 'barbarian',
  Ranger = 'ranger'
}

export enum AnimationState {
  Idle = 'idle',
  Walking = 'walking',
  Running = 'running',
  Attacking = 'attacking',
  Casting = 'casting',
  Hurt = 'hurt',
  Dying = 'dying',
  Dead = 'dead'
}

export interface StatusEffect {
  id: string
  name: string
  duration: number
  icon?: string
  color?: string
  particleEffect?: string
}

export interface Spell {
  id: string
  name: string
  type: SpellType
  damage?: number
  healing?: number
  duration?: number
  radius?: number
  speed?: number
  color?: number
  castTime: number
  particleEffect: ParticleEffectConfig
  soundEffect?: string
}

export enum SpellType {
  Damage = 'damage',
  Healing = 'healing',
  Buff = 'buff',
  Debuff = 'debuff',
  Illusion = 'illusion',
  Summoning = 'summoning'
}

export interface ParticleEffectConfig {
  type: ParticleType
  count: number
  lifespan: number
  speed: number
  size: number
  color?: number
  colors?: number[]
  gravity?: number
  spread?: number
  rotation?: THREE.Vector3
  texture?: string
}

export enum ParticleType {
  Fire = 'fire',
  Lightning = 'lightning',
  Healing = 'healing',
  Ice = 'ice',
  Earth = 'earth',
  Wind = 'wind',
  Blood = 'blood',
  Magic = 'magic',
  Smoke = 'smoke',
  Explosion = 'explosion'
}

export interface CombatEvent {
  id: string
  type: CombatEventType
  source: Character
  target?: Character
  spell?: Spell
  damage?: number
  healing?: number
  critical?: boolean
  miss?: boolean
  position: THREE.Vector3
  timestamp: number
}

export enum CombatEventType {
  Attack = 'attack',
  SpellCast = 'spellCast',
  Damage = 'damage',
  Healing = 'healing',
  Miss = 'miss',
  CriticalHit = 'criticalHit',
  StatusEffectApplied = 'statusEffectApplied',
  Death = 'death'
}

export interface EnvironmentObject {
  id: string
  type: EnvironmentType
  position: THREE.Vector3
  rotation: THREE.Euler
  scale: THREE.Vector3
  destructible: boolean
  health?: number
  mesh?: THREE.Object3D
}

export enum EnvironmentType {
  Tree = 'tree',
  Rock = 'rock',
  Wall = 'wall',
  Barrel = 'barrel',
  Crate = 'crate',
  Statue = 'statue',
  Pillar = 'pillar'
}

export interface CameraSettings {
  position: THREE.Vector3
  target: THREE.Vector3
  fov: number
  near: number
  far: number
  type: 'perspective' | 'orthographic'
}

export interface SceneConfig {
  gridSize: number
  cellSize: number
  terrainType: TerrainType
  lighting: LightingConfig
  weather?: WeatherConfig
  timeOfDay: number // 0-24 hours
}

export enum TerrainType {
  Grass = 'grass',
  Stone = 'stone',
  Sand = 'sand',
  Snow = 'snow',
  Dungeon = 'dungeon'
}

export interface LightingConfig {
  ambientIntensity: number
  ambientColor: number
  directionalIntensity: number
  directionalColor: number
  directionalPosition: THREE.Vector3
  shadows: boolean
}

export interface WeatherConfig {
  type: WeatherType
  intensity: number
  particleConfig?: ParticleEffectConfig
}

export enum WeatherType {
  Clear = 'clear',
  Rain = 'rain',
  Snow = 'snow',
  Fog = 'fog',
  Storm = 'storm'
}

export interface AnimationClip {
  name: string
  duration: number
  loop: boolean
  keyframes: Keyframe[]
}

export interface Keyframe {
  time: number
  position?: THREE.Vector3
  rotation?: THREE.Euler
  scale?: THREE.Vector3
  opacity?: number
}

// Performance and optimization types
export interface PerformanceConfig {
  maxParticles: number
  lodDistance: number
  shadowMapSize: number
  antialias: boolean
  pixelRatio: number
}

export interface EffectQueue {
  effects: QueuedEffect[]
  maxConcurrent: number
}

export interface QueuedEffect {
  id: string
  type: string
  config: any
  priority: number
  timestamp: number
}