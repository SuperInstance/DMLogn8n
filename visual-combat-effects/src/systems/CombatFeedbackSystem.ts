import * as THREE from 'three'
import { CombatEvent, CombatEventType } from '@/types'
import { gsap } from 'gsap'

export interface DamageNumber {
  id: string
  value: number
  position: THREE.Vector3
  color: string
  size: number
  critical: boolean
  healing: boolean
  mesh?: THREE.Mesh
  opacity: number
  velocity: THREE.Vector3
}

export interface MissIndicator {
  id: string
  position: THREE.Vector3
  mesh?: THREE.Mesh
  opacity: number
  rotation: number
}

export interface StatusEffectVisual {
  id: string
  characterId: string
  effectName: string
  position: THREE.Vector3
  icon?: string
  color: string
  mesh?: THREE.Mesh
  duration: number
  maxDuration: number
}

export interface CombatLogEntry {
  id: string
  message: string
  type: CombatEventType
  timestamp: number
  source: string
  target?: string
  value?: number
  critical?: boolean
}

export class CombatFeedbackSystem {
  private scene: THREE.Scene
  private camera: THREE.Camera
  private damageNumbers: Map<string, DamageNumber> = new Map()
  private missIndicators: Map<string, MissIndicator> = new Map()
  private statusEffects: Map<string, StatusEffectVisual> = new Map()
  private combatLog: CombatLogEntry[] = []
  private maxCombatLogEntries: number = 50

  constructor(scene: THREE.Scene, camera: THREE.Camera) {
    this.scene = scene
    this.camera = camera
  }

  public showDamageNumber(
    value: number,
    position: THREE.Vector3,
    critical: boolean = false,
    healing: boolean = false
  ): void {
    const id = `damage_${Date.now()}_${Math.random()}`
    const damageNumber: DamageNumber = {
      id,
      value,
      position: position.clone(),
      color: this.getDamageNumberColor(healing, critical),
      size: this.getDamageNumberSize(critical),
      critical,
      healing,
      opacity: 1,
      velocity: new THREE.Vector3(
        (Math.random() - 0.5) * 2,
        2 + (critical ? 2 : 0),
        0
      )
    }

    this.createDamageNumberMesh(damageNumber)
    this.damageNumbers.set(id, damageNumber)

    // Animate the damage number
    this.animateDamageNumber(damageNumber)
  }

  public showMissIndicator(position: THREE.Vector3): void {
    const id = `miss_${Date.now()}_${Math.random()}`
    const missIndicator: MissIndicator = {
      id,
      position: position.clone(),
      opacity: 1,
      rotation: 0
    }

    this.createMissIndicatorMesh(missIndicator)
    this.missIndicators.set(id, missIndicator)

    // Animate the miss indicator
    this.animateMissIndicator(missIndicator)
  }

  public addStatusEffect(
    characterId: string,
    effectName: string,
    position: THREE.Vector3,
    duration: number,
    color: string = '#ffff00'
  ): void {
    const id = `status_${characterId}_${effectName}`
    const statusEffect: StatusEffectVisual = {
      id,
      characterId,
      effectName,
      position: position.clone(),
      color,
      duration,
      maxDuration: duration
    }

    this.createStatusEffectMesh(statusEffect)
    this.statusEffects.set(id, statusEffect)

    // Animate status effect
    this.animateStatusEffect(statusEffect)
  }

  public removeStatusEffect(characterId: string, effectName: string): void {
    const id = `status_${characterId}_${effectName}`
    const statusEffect = this.statusEffects.get(id)
    if (statusEffect) {
      this.removeStatusEffectVisual(statusEffect)
      this.statusEffects.delete(id)
    }
  }

  public updateStatusEffectDuration(characterId: string, effectName: string, newDuration: number): void {
    const id = `status_${characterId}_${effectName}`
    const statusEffect = this.statusEffects.get(id)
    if (statusEffect) {
      statusEffect.duration = newDuration
      this.updateStatusEffectVisual(statusEffect)
    }
  }

  public addCombatLogEntry(event: CombatEvent): void {
    const entry: CombatLogEntry = {
      id: `log_${Date.now()}_${Math.random()}`,
      message: this.generateCombatLogMessage(event),
      type: event.type,
      timestamp: event.timestamp,
      source: event.source.name,
      target: event.target?.name,
      value: event.damage || event.healing,
      critical: event.critical
    }

    this.combatLog.unshift(entry)

    // Keep only the most recent entries
    if (this.combatLog.length > this.maxCombatLogEntries) {
      this.combatLog = this.combatLog.slice(0, this.maxCombatLogEntries)
    }

    // Notify listeners of new combat log entry
    this.onCombatLogEntryAdded(entry)
  }

  private getDamageNumberColor(healing: boolean, critical: boolean): string {
    if (healing) {
      return '#00ff00' // Green for healing
    } else if (critical) {
      return '#ff0000' // Red for critical hits
    } else {
      return '#ffff00' // Yellow for normal damage
    }
  }

  private getDamageNumberSize(critical: boolean): number {
    return critical ? 1.5 : 1.0
  }

  private createDamageNumberMesh(damageNumber: DamageNumber): void {
    // Create text sprite for damage number
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')!
    canvas.width = 256
    canvas.height = 128

    // Set font and style
    const fontSize = damageNumber.critical ? 72 : 48
    context.font = `bold ${fontSize}px Arial`
    context.fillStyle = damageNumber.color
    context.strokeStyle = '#000000'
    context.lineWidth = 3
    context.textAlign = 'center'
    context.textBaseline = 'middle'

    // Add shadow for better readability
    context.shadowColor = 'rgba(0, 0, 0, 0.8)'
    context.shadowBlur = 4
    context.shadowOffsetX = 2
    context.shadowOffsetY = 2

    // Draw text
    const text = damageNumber.healing ? `+${damageNumber.value}` : `-${damageNumber.value}`
    context.fillText(text, 128, 64)
    context.strokeText(text, 128, 64)

    // Add critical hit indicator
    if (damageNumber.critical) {
      context.font = 'bold 24px Arial'
      context.fillStyle = '#ff9900'
      context.fillText('CRITICAL!', 128, 100)
    }

    // Create texture and sprite
    const texture = new THREE.CanvasTexture(canvas)
    const spriteMaterial = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      alphaTest: 0.1
    })
    const sprite = new THREE.Sprite(spriteMaterial)

    // Set size based on viewport
    const distance = this.camera.position.distanceTo(damageNumber.position)
    const scale = damageNumber.size * 0.1 * distance
    sprite.scale.set(scale, scale * 0.5, 1)

    sprite.position.copy(damageNumber.position)
    sprite.renderOrder = 1000 // Ensure it renders on top

    this.scene.add(sprite)
    damageNumber.mesh = sprite as any
  }

  private createMissIndicatorMesh(missIndicator: MissIndicator): void {
    // Create "MISS" text sprite
    const canvas = document.createElement('canvas')
    const context = canvas.getContext('2d')!
    canvas.width = 256
    canvas.height = 64

    context.font = 'bold 48px Arial'
    context.fillStyle = '#808080'
    context.strokeStyle = '#000000'
    context.lineWidth = 3
    context.textAlign = 'center'
    context.textBaseline = 'middle'

    context.shadowColor = 'rgba(0, 0, 0, 0.8)'
    context.shadowBlur = 4
    context.shadowOffsetX = 2
    context.shadowOffsetY = 2

    context.fillText('MISS', 128, 32)
    context.strokeText('MISS', 128, 32)

    const texture = new THREE.CanvasTexture(canvas)
    const spriteMaterial = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      opacity: 0.8
    })
    const sprite = new THREE.Sprite(spriteMaterial)

    const distance = this.camera.position.distanceTo(missIndicator.position)
    const scale = 0.08 * distance
    sprite.scale.set(scale, scale * 0.25, 1)

    sprite.position.copy(missIndicator.position)
    sprite.renderOrder = 1000

    this.scene.add(sprite)
    missIndicator.mesh = sprite as any
  }

  private createStatusEffectMesh(statusEffect: StatusEffectVisual): void {
    // Create status effect icon above character
    const geometry = new THREE.PlaneGeometry(0.8, 0.8)
    const material = new THREE.MeshBasicMaterial({
      color: statusEffect.color,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    })
    const mesh = new THREE.Mesh(geometry, material)

    // Position above character
    mesh.position.copy(statusEffect.position)
    mesh.position.y += 3

    // Add border
    const borderGeometry = new THREE.EdgesGeometry(geometry)
    const borderMaterial = new THREE.LineBasicMaterial({
      color: 0x000000,
      linewidth: 2
    })
    const border = new THREE.LineSegments(borderGeometry, borderMaterial)
    mesh.add(border)

    this.scene.add(mesh)
    statusEffect.mesh = mesh

    // Create duration indicator
    this.createDurationIndicator(statusEffect)
  }

  private createDurationIndicator(statusEffect: StatusEffectVisual): void {
    // Create a small ring showing remaining duration
    const radius = 0.5
    const segments = 32
    const thetaLength = (statusEffect.duration / statusEffect.maxDuration) * Math.PI * 2

    const geometry = new THREE.RingGeometry(radius - 0.05, radius, segments, 1, 0, thetaLength)
    const material = new THREE.MeshBasicMaterial({
      color: 0x00ff00,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    })
    const durationRing = new THREE.Mesh(geometry, material)

    durationRing.position.copy(statusEffect.mesh!.position)
    durationRing.position.y += 0.6
    durationRing.rotation.x = -Math.PI / 2

    this.scene.add(durationRing)

    // Store reference for updating
    statusEffect.mesh!.userData.durationRing = durationRing
  }

  private animateDamageNumber(damageNumber: DamageNumber): void {
    if (!damageNumber.mesh) return

    const timeline = gsap.timeline()

    // Move upward and fade out
    timeline.to(damageNumber.position, {
      y: damageNumber.position.y + 3,
      duration: 1.5,
      ease: "power2.out"
    })

    // Slight horizontal movement
    timeline.to(damageNumber.position, {
      x: damageNumber.position.x + damageNumber.velocity.x,
      duration: 1.5,
      ease: "power2.out"
    }, 0)

    // Fade out
    timeline.to(damageNumber, {
      opacity: 0,
      duration: 0.5,
      ease: "power2.in",
      onUpdate: () => {
        if (damageNumber.mesh) {
          (damageNumber.mesh as THREE.Sprite).material.opacity = damageNumber.opacity
        }
      },
      onComplete: () => {
        this.removeDamageNumber(damageNumber.id)
      }
    }, 1)

    // Scale animation for critical hits
    if (damageNumber.critical) {
      timeline.to(damageNumber.mesh!.scale, {
        x: damageNumber.mesh!.scale.x * 1.5,
        y: damageNumber.mesh!.scale.y * 1.5,
        duration: 0.2,
        ease: "back.out(1.7)",
        yoyo: true,
        repeat: 1
      }, 0)
    }
  }

  private animateMissIndicator(missIndicator: MissIndicator): void {
    if (!missIndicator.mesh) return

    const timeline = gsap.timeline()

    // Shake effect
    timeline.to(missIndicator.mesh!.position, {
      x: missIndicator.mesh!.position.x + 0.1,
      duration: 0.05,
      repeat: 5,
      yoyo: true,
      ease: "none"
    })

    // Fade out
    timeline.to(missIndicator, {
      opacity: 0,
      duration: 0.8,
      ease: "power2.in",
      onUpdate: () => {
        if (missIndicator.mesh) {
          (missIndicator.mesh as THREE.Sprite).material.opacity = missIndicator.opacity
        }
      },
      onComplete: () => {
        this.removeMissIndicator(missIndicator.id)
      }
    }, 0.5)
  }

  private animateStatusEffect(statusEffect: StatusEffectVisual): void {
    if (!statusEffect.mesh) return

    // Floating animation
    const startY = statusEffect.mesh.position.y
    gsap.to(statusEffect.mesh.position, {
      y: startY + 0.2,
      duration: 1.5,
      ease: "sine.inOut",
      repeat: -1,
      yoyo: true
    })

    // Rotation animation
    gsap.to(statusEffect.mesh.rotation, {
      y: Math.PI * 2,
      duration: 4,
      ease: "none",
      repeat: -1
    })

    // Pulsing effect
    gsap.to(statusEffect.mesh.scale, {
      x: 1.1,
      y: 1.1,
      z: 1.1,
      duration: 1,
      ease: "sine.inOut",
      repeat: -1,
      yoyo: true
    })
  }

  private updateStatusEffectVisual(statusEffect: StatusEffectVisual): void {
    if (!statusEffect.mesh) return

    const durationRing = statusEffect.mesh.userData.durationRing
    if (durationRing) {
      const ratio = Math.max(0, statusEffect.duration / statusEffect.maxDuration)
      const thetaLength = ratio * Math.PI * 2

      // Update ring geometry
      const geometry = new THREE.RingGeometry(0.45, 0.5, 32, 1, 0, thetaLength)
      durationRing.geometry.dispose()
      durationRing.geometry = geometry

      // Update color based on remaining time
      const material = durationRing.material as THREE.MeshBasicMaterial
      if (ratio > 0.5) {
        material.color.setHex(0x00ff00) // Green
      } else if (ratio > 0.25) {
        material.color.setHex(0xffff00) // Yellow
      } else {
        material.color.setHex(0xff0000) // Red
      }
    }

    // Remove effect if duration expired
    if (statusEffect.duration <= 0) {
      this.removeStatusEffectVisual(statusEffect)
      this.statusEffects.delete(statusEffect.id)
    }
  }

  private removeStatusEffectVisual(statusEffect: StatusEffectVisual): void {
    if (statusEffect.mesh) {
      // Fade out animation
      gsap.to(statusEffect.mesh.scale, {
        x: 0,
        y: 0,
        z: 0,
        duration: 0.3,
        ease: "back.in",
        onComplete: () => {
          this.scene.remove(statusEffect.mesh!)
          statusEffect.mesh!.traverse((child) => {
            if (child instanceof THREE.Mesh) {
              child.geometry.dispose()
              if (child.material instanceof THREE.Material) {
                child.material.dispose()
              }
            }
          })
        }
      })

      // Remove duration ring if exists
      const durationRing = statusEffect.mesh.userData.durationRing
      if (durationRing) {
        this.scene.remove(durationRing)
        durationRing.geometry.dispose()
        (durationRing.material as THREE.Material).dispose()
      }
    }
  }

  private removeDamageNumber(id: string): void {
    const damageNumber = this.damageNumbers.get(id)
    if (damageNumber && damageNumber.mesh) {
      this.scene.remove(damageNumber.mesh)
      if (damageNumber.mesh.material instanceof THREE.Material) {
        damageNumber.mesh.material.dispose()
      }
      if (damageNumber.mesh.material.map) {
        damageNumber.mesh.material.map.dispose()
      }
    }
    this.damageNumbers.delete(id)
  }

  private removeMissIndicator(id: string): void {
    const missIndicator = this.missIndicators.get(id)
    if (missIndicator && missIndicator.mesh) {
      this.scene.remove(missIndicator.mesh)
      if (missIndicator.mesh.material instanceof THREE.Material) {
        missIndicator.mesh.material.dispose()
      }
      if (missIndicator.mesh.material.map) {
        missIndicator.mesh.material.map.dispose()
      }
    }
    this.missIndicators.delete(id)
  }

  private generateCombatLogMessage(event: CombatEvent): string {
    switch (event.type) {
      case CombatEventType.Attack:
        if (event.miss) {
          return `${event.source.name} attacks ${event.target?.name} but misses!`
        } else if (event.critical) {
          return `${event.source.name} lands a CRITICAL hit on ${event.target?.name} for ${event.damage} damage!`
        } else {
          return `${event.source.name} hits ${event.target?.name} for ${event.damage} damage.`
        }
      case CombatEventType.SpellCast:
        return `${event.source.name} casts ${event.spell?.name}${event.target ? ` on ${event.target.name}` : ''}.`
      case CombatEventType.Damage:
        return `${event.source.name} deals ${event.damage} damage to ${event.target?.name}.`
      case CombatEventType.Healing:
        return `${event.source.name} heals ${event.target?.name} for ${event.healing} health.`
      case CombatEventType.StatusEffectApplied:
        return `${event.source.name} applies ${event.spell?.name} to ${event.target?.name}.`
      case CombatEventType.Death:
        return `${event.source.name} has been defeated!`
      default:
        return `${event.source.name} performs an action.`
    }
  }

  private onCombatLogEntryAdded(entry: CombatLogEntry): void {
    // This can be used to trigger UI updates
    // Implementation would depend on the UI framework being used
    console.log(`Combat Log: ${entry.message}`)
  }

  public update(deltaTime: number): void {
    // Update status effects durations
    this.statusEffects.forEach(statusEffect => {
      statusEffect.duration -= deltaTime
      this.updateStatusEffectVisual(statusEffect)
    })

    // Update damage numbers positions based on camera
    this.damageNumbers.forEach(damageNumber => {
      if (damageNumber.mesh) {
        // Make damage numbers always face the camera
        damageNumber.mesh.lookAt(this.camera.position)
      }
    })

    this.missIndicators.forEach(missIndicator => {
      if (missIndicator.mesh) {
        // Make miss indicators always face the camera
        missIndicator.mesh.lookAt(this.camera.position)
      }
    })
  }

  public getCombatLog(): CombatLogEntry[] {
    return [...this.combatLog]
  }

  public clearCombatLog(): void {
    this.combatLog = []
  }

  public clearAllVisuals(): void {
    // Remove all damage numbers
    this.damageNumbers.forEach((_, id) => this.removeDamageNumber(id))
    this.damageNumbers.clear()

    // Remove all miss indicators
    this.missIndicators.forEach((_, id) => this.removeMissIndicator(id))
    this.missIndicators.clear()

    // Remove all status effects
    this.statusEffects.forEach(statusEffect => {
      this.removeStatusEffectVisual(statusEffect)
    })
    this.statusEffects.clear()
  }

  public dispose(): void {
    this.clearAllVisuals()
    this.clearCombatLog()
  }
}