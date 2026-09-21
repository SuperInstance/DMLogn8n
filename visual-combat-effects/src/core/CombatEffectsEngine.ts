import * as THREE from 'three'
import { CombatScene } from './Scene'
import { CharacterAnimator } from '@/animations/CharacterAnimator'
import { SpellEffectsManager } from '@/effects/SpellEffects'
import { CombatFeedbackSystem } from '@/systems/CombatFeedbackSystem'
import { EnvironmentalSystem } from '@/systems/EnvironmentalSystem'
import { Character, Spell, CombatEvent, SpellType, PerformanceConfig } from '@/types'

export class CombatEffectsEngine {
  public scene: CombatScene
  public camera: THREE.Camera
  private characters: Map<string, CharacterAnimator> = new Map()
  private spellEffectsManager: SpellEffectsManager
  private combatFeedbackSystem: CombatFeedbackSystem
  private environmentalSystem: EnvironmentalSystem

  private performanceConfig: PerformanceConfig
  private isRunning: boolean = false
  private lastTime: number = 0
  private frameCount: number = 0
  private fps: number = 60
  private lastFpsUpdate: number = 0

  // Performance monitoring
  private performanceMonitor: {
    activeParticles: number
    activeEffects: number
    drawCalls: number
    triangles: number
    memoryUsage?: number
  }

  constructor(canvas: HTMLCanvasElement) {
    // Initialize scene
    const sceneConfig = {
      gridSize: 20,
      cellSize: 1,
      terrainType: 'grass' as any,
      lighting: {
        ambientIntensity: 0.4,
        ambientColor: 0x404040,
        directionalIntensity: 0.8,
        directionalColor: 0xffffff,
        directionalPosition: new THREE.Vector3(10, 20, 10),
        shadows: true
      },
      timeOfDay: 12
    }

    const cameraSettings = {
      position: new THREE.Vector3(15, 20, 15),
      target: new THREE.Vector3(0, 0, 0),
      fov: 60,
      near: 0.1,
      far: 1000,
      type: 'perspective' as const
    }

    this.scene = new CombatScene(sceneConfig, cameraSettings)
    this.camera = this.scene.camera

    // Initialize subsystems
    this.spellEffectsManager = new SpellEffectsManager(this.scene.scene)
    this.combatFeedbackSystem = new CombatFeedbackSystem(this.scene.scene, this.camera)
    this.environmentalSystem = new EnvironmentalSystem(this.scene.scene)

    // Set up performance configuration
    this.performanceConfig = {
      maxParticles: 1000,
      lodDistance: 50,
      shadowMapSize: 2048,
      antialias: true,
      pixelRatio: Math.min(window.devicePixelRatio, 2)
    }

    // Initialize performance monitor
    this.performanceMonitor = {
      activeParticles: 0,
      activeEffects: 0,
      drawCalls: 0,
      triangles: 0
    }

    this.setupRenderer()
    this.setupEventListeners()
  }

  private setupRenderer(): void {
    // Apply performance settings
    this.scene.renderer.setPixelRatio(this.performanceConfig.pixelRatio)
    this.scene.renderer.shadowMap.enabled = true

    if (this.scene.renderer.capabilities.isWebGL2) {
      // Enable advanced features for WebGL2
      this.scene.renderer.outputColorSpace = THREE.SRGBColorSpace
      this.scene.renderer.toneMapping = THREE.ACESFilmicToneMapping
      this.scene.renderer.toneMappingExposure = 1.2
    }
  }

  private setupEventListeners(): void {
    window.addEventListener('resize', () => this.handleResize())
    document.addEventListener('visibilitychange', () => this.handleVisibilityChange())
  }

  private handleResize(): void {
    const width = window.innerWidth
    const height = window.innerHeight

    this.scene.resize(width, height)

    // Adjust quality based on viewport size
    if (width < 768) {
      this.setQualityLevel('low')
    } else if (width < 1200) {
      this.setQualityLevel('medium')
    } else {
      this.setQualityLevel('high')
    }
  }

  private handleVisibilityChange(): void {
    if (document.hidden) {
      this.pause()
    } else {
      this.resume()
    }
  }

  public start(): void {
    this.isRunning = true
    this.lastTime = performance.now()
    this.animate()
  }

  public pause(): void {
    this.isRunning = false
  }

  public resume(): void {
    if (!this.isRunning) {
      this.isRunning = true
      this.lastTime = performance.now()
      this.animate()
    }
  }

  public stop(): void {
    this.isRunning = false
    this.dispose()
  }

  private animate(): void {
    if (!this.isRunning) return

    const currentTime = performance.now()
    const deltaTime = (currentTime - this.lastTime) / 1000
    this.lastTime = currentTime

    // Update FPS counter
    this.updateFPS(currentTime)

    // Update all systems
    this.update(deltaTime)

    // Update performance monitoring
    this.updatePerformanceMetrics()

    // Render the scene
    this.scene.render()

    // Continue animation loop
    requestAnimationFrame(() => this.animate())
  }

  private updateFPS(currentTime: number): void {
    this.frameCount++

    if (currentTime - this.lastFpsUpdate >= 1000) {
      this.fps = this.frameCount
      this.frameCount = 0
      this.lastFpsUpdate = currentTime

      // Adjust quality based on performance
      this.adjustQualityBasedOnPerformance()
    }
  }

  private updatePerformanceMetrics(): void {
    if (this.scene.renderer.info) {
      this.performanceMonitor.drawCalls = this.scene.renderer.info.render.calls
      this.performanceMonitor.triangles = this.scene.renderer.info.render.triangles
    }

    // Estimate active particles (rough calculation)
    this.performanceMonitor.activeParticles = this.spellEffectsManager['particleSystems'].size * 50

    // Estimate active effects
    this.performanceMonitor.activeEffects =
      this.characters.size +
      this.spellEffectsManager['activeSpells'].size +
      this.combatFeedbackSystem['damageNumbers'].size

    // Memory usage (if available)
    if ((performance as any).memory) {
      this.performanceMonitor.memoryUsage = (performance as any).memory.usedJSHeapSize / 1048576 // MB
    }
  }

  private adjustQualityBasedOnPerformance(): void {
    if (this.fps < 30) {
      // Performance is poor, reduce quality
      if (this.performanceConfig.maxParticles > 500) {
        this.setQualityLevel('low')
      }
    } else if (this.fps > 50) {
      // Performance is good, can increase quality
      if (this.performanceConfig.maxParticles < 1000) {
        this.setQualityLevel('high')
      }
    }
  }

  private update(deltaTime: number): void {
    // Update character animations
    this.characters.forEach(animator => {
      animator.update(deltaTime)
    })

    // Update spell effects
    this.spellEffectsManager.update(deltaTime)

    // Update combat feedback
    this.combatFeedbackSystem.update(deltaTime)

    // Update environment
    this.environmentSystem.update(deltaTime)

    // Update scene
    this.scene.updateEnvironment(deltaTime)
  }

  public addCharacter(character: Character): void {
    // Create character mesh
    const characterGroup = new THREE.Group()
    characterGroup.position.copy(character.position)
    characterGroup.name = character.id

    this.scene.scene.add(characterGroup)

    // Create animator
    const animator = new CharacterAnimator(character, characterGroup)
    animator.playAnimation('idle')

    this.characters.set(character.id, animator)
    character.mesh = characterGroup
  }

  public removeCharacter(characterId: string): void {
    const animator = this.characters.get(characterId)
    if (animator) {
      const character = animator['character']
      if (character.mesh) {
        this.scene.scene.remove(character.mesh)
      }
      animator.dispose()
      this.characters.delete(characterId)
    }
  }

  public moveCharacter(characterId: string, targetPosition: THREE.Vector3, speed: number = 2): Promise<void> {
    const animator = this.characters.get(characterId)
    if (!animator) {
      return Promise.resolve()
    }

    return animator.moveToPosition(targetPosition, speed)
  }

  public characterAttack(attackerId: string, targetId: string): Promise<void> {
    const attackerAnimator = this.characters.get(attackerId)
    const targetAnimator = this.characters.get(targetId)

    if (!attackerAnimator || !targetAnimator) {
      return Promise.resolve()
    }

    return attackerAnimator.playAttackAnimation(targetAnimator['character'].position)
  }

  public castSpell(casterId: string, spell: Spell, targetPosition?: THREE.Vector3, targetId?: string): Promise<void> {
    const casterAnimator = this.characters.get(casterId)
    if (!casterAnimator) {
      return Promise.resolve()
    }

    // Play cast animation
    return casterAnimator.playCastAnimation().then(() => {
      // Create spell effect
      const spellVisual = {
        id: `spell_${Date.now()}_${Math.random()}`,
        spell,
        startPosition: casterAnimator['character'].position.clone(),
        endPosition: targetPosition,
        target: targetId ? this.characters.get(targetId)?.['character'].mesh : undefined
      }

      this.spellEffectsManager.castSpell(spellVisual)

      // Create combat event
      const combatEvent: CombatEvent = {
        id: spellVisual.id,
        type: CombatEventType.SpellCast,
        source: casterAnimator['character'],
        target: targetId ? this.characters.get(targetId)?.['character'] : undefined,
        spell,
        position: targetPosition || casterAnimator['character'].position,
        timestamp: Date.now()
      }

      this.combatFeedbackSystem.addCombatLogEntry(combatEvent)

      // Simulate spell impact after travel time
      const impactDelay = spell.speed ? spell.speed * 1000 : 1000
      setTimeout(() => {
        this.resolveSpellImpact(spellVisual)
      }, impactDelay)
    })
  }

  private resolveSpellImpact(spellVisual: any): void {
    const { spell, endPosition, target } = spellVisual

    if (target) {
      // Apply damage or healing to target
      if (spell.damage) {
        this.showDamage(spell.damage, endPosition, false, false)

        const combatEvent: CombatEvent = {
          id: `${spellVisual.id}_impact`,
          type: CombatEventType.Damage,
          source: spellVisual.source,
          target: spellVisual.target,
          spell,
          damage: spell.damage,
          position: endPosition,
          timestamp: Date.now()
        }
        this.combatFeedbackSystem.addCombatLogEntry(combatEvent)
      } else if (spell.healing) {
        this.showDamage(spell.healing, endPosition, false, true)

        const combatEvent: CombatEvent = {
          id: `${spellVisual.id}_impact`,
          type: CombatEventType.Healing,
          source: spellVisual.source,
          target: spellVisual.target,
          spell,
          healing: spell.healing,
          position: endPosition,
          timestamp: Date.now()
        }
        this.combatFeedbackSystem.addCombatLogEntry(combatEvent)
      }

      // Add status effect if applicable
      if (spell.type === SpellType.Buff || spell.type === SpellType.Debuff) {
        const targetCharacter = this.findCharacterByMesh(target)
        if (targetCharacter) {
          this.combatFeedbackSystem.addStatusEffect(
            targetCharacter.id,
            spell.name,
            targetCharacter.position,
            spell.duration || 10,
            spell.color ? `#${spell.color.toString(16)}` : '#ffff00'
          )
        }
      }
    }
  }

  private findCharacterByMesh(mesh: THREE.Object3D): Character | null {
    for (const [id, animator] of this.characters) {
      if (animator['character'].mesh === mesh) {
        return animator['character']
      }
    }
    return null
  }

  public showDamage(damage: number, position: THREE.Vector3, critical: boolean = false, healing: boolean = false): void {
    this.combatFeedbackSystem.showDamageNumber(damage, position, critical, healing)
  }

  public showMiss(position: THREE.Vector3): void {
    this.combatFeedbackSystem.showMissIndicator(position)
  }

  public damageEnvironment(objectId: string, damage: number): boolean {
    return this.environmentalSystem.damageEnvironmentObject(objectId, damage)
  }

  public setWeather(weather: any): void {
    this.environmentalSystem.setWeather(weather)
  }

  public setDayNightCycle(enabled: boolean, speed: number = 0.1): void {
    this.environmentalSystem.setDayNightCycle(enabled, speed)
  }

  public setTimeOfDay(hour: number): void {
    this.environmentalSystem.setTimeOfDay(hour)
  }

  public setCameraPosition(position: THREE.Vector3, target?: THREE.Vector3): void {
    this.camera.position.copy(position)
    if (target) {
      this.camera.lookAt(target)
    }
  }

  public setQualityLevel(level: 'low' | 'medium' | 'high'): void {
    switch (level) {
      case 'low':
        this.performanceConfig.maxParticles = 500
        this.performanceConfig.shadowMapSize = 1024
        this.performanceConfig.antialias = false
        this.performanceConfig.pixelRatio = 1
        break

      case 'medium':
        this.performanceConfig.maxParticles = 750
        this.performanceConfig.shadowMapSize = 2048
        this.performanceConfig.antialias = true
        this.performanceConfig.pixelRatio = 1.5
        break

      case 'high':
        this.performanceConfig.maxParticles = 1000
        this.performanceConfig.shadowMapSize = 4096
        this.performanceConfig.antialias = true
        this.performanceConfig.pixelRatio = Math.min(window.devicePixelRatio, 2)
        break
    }

    // Apply settings
    this.scene.renderer.setPixelRatio(this.performanceConfig.pixelRatio)
    this.scene.renderer.shadowMap.enabled = this.performanceConfig.shadowMapSize > 0

    if (this.scene.renderer.shadowMap.enabled) {
      const light = this.scene.scene.children.find(
        child => child instanceof THREE.DirectionalLight
      ) as THREE.DirectionalLight

      if (light && light.shadow.map) {
        light.shadow.mapSize.width = this.performanceConfig.shadowMapSize
        light.shadow.mapSize.height = this.performanceConfig.shadowMapSize
        light.shadow.map?.dispose()
        light.shadow.map = null
      }
    }
  }

  public getPerformanceMetrics(): any {
    return {
      ...this.performanceMonitor,
      fps: this.fps,
      qualityLevel: this.getCurrentQualityLevel(),
      activeCharacters: this.characters.size,
      memoryPerformance: this.getMemoryPerformance()
    }
  }

  private getCurrentQualityLevel(): string {
    if (this.performanceConfig.maxParticles <= 500) return 'low'
    if (this.performanceConfig.maxParticles <= 750) return 'medium'
    return 'high'
  }

  private getMemoryPerformance(): any {
    if (!(performance as any).memory) {
      return { available: false }
    }

    const memory = (performance as any).memory
    return {
      available: true,
      used: Math.round(memory.usedJSHeapSize / 1048576), // MB
      total: Math.round(memory.totalJSHeapSize / 1048576), // MB
      limit: Math.round(memory.jsHeapSizeLimit / 1048576) // MB
    }
  }

  public exportScene(): any {
    const sceneData = {
      characters: Array.from(this.characters.values()).map(animator => ({
        id: animator['character'].id,
        name: animator['character'].name,
        class: animator['character'].class,
        position: animator['character'].position,
        health: animator['character'].health,
        animationState: animator['character'].animationState
      })),
      environment: this.environmentalSystem.getAllEnvironmentObjects().map(obj => ({
        id: obj.id,
        type: obj.type,
        position: obj.position,
        health: obj.health
      })),
      timeOfDay: this.environmentalSystem['timeOfDay'],
      performance: this.getPerformanceMetrics()
    }

    return sceneData
  }

  public importScene(sceneData: any): void {
    // Clear existing scene
    this.characters.forEach(animator => this.removeCharacter(animator['character'].id))

    // Import characters
    sceneData.characters?.forEach((charData: any) => {
      const character: Character = {
        id: charData.id,
        name: charData.name,
        class: charData.class,
        position: new THREE.Vector3(charData.position.x, charData.position.y, charData.position.z),
        rotation: 0,
        health: charData.health,
        maxHealth: charData.health,
        level: 1,
        animationState: charData.animationState,
        statusEffects: []
      }
      this.addCharacter(character)
    })

    // Import environment
    sceneData.environment?.forEach((envData: any) => {
      // This would require the environment system to support importing
      console.log('Importing environment object:', envData)
    })

    // Import time of day
    if (sceneData.timeOfDay !== undefined) {
      this.setTimeOfDay(sceneData.timeOfDay)
    }
  }

  public dispose(): void {
    // Dispose all systems
    this.characters.forEach(animator => animator.dispose())
    this.characters.clear()

    this.spellEffectsManager.dispose()
    this.combatFeedbackSystem.dispose()
    this.environmentalSystem.dispose()
    this.scene.dispose()

    // Remove event listeners
    window.removeEventListener('resize', this.handleResize)
    document.removeEventListener('visibilitychange', this.handleVisibilityChange)
  }
}