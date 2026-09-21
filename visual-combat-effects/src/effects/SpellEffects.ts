import * as THREE from 'three'
import { Spell, SpellType } from '@/types'
import {
  ParticleSystem,
  FireballEffect,
  LightningEffect,
  HealingEffect,
  ExplosionEffect
} from './ParticleSystem'
import { gsap } from 'gsap'

export interface SpellVisual {
  id: string
  spell: Spell
  startPosition: THREE.Vector3
  endPosition?: THREE.Vector3
  target?: THREE.Object3D
  onComplete?: () => void
}

export class SpellEffectsManager {
  private scene: THREE.Scene
  private activeSpells: Map<string, SpellVisual> = new Map()
  private particleSystems: Map<string, ParticleSystem> = new Map()
  private meshes: Map<string, THREE.Object3D> = new Map()
  private timelines: Map<string, gsap.core.Timeline> = new Map()

  constructor(scene: THREE.Scene) {
    this.scene = scene
  }

  public castSpell(spellVisual: SpellVisual): void {
    this.activeSpells.set(spellVisual.id, spellVisual)

    switch (spell.spell.type) {
      case SpellType.Damage:
        this.castDamageSpell(spellVisual)
        break
      case SpellType.Healing:
        this.castHealingSpell(spellVisual)
        break
      case SpellType.Buff:
        this.castBuffSpell(spellVisual)
        break
      case SpellType.Debuff:
        this.castDebuffSpell(spellVisual)
        break
      case SpellType.Illusion:
        this.castIllusionSpell(spellVisual)
        break
      case SpellType.Summoning:
        this.castSummoningSpell(spellVisual)
        break
    }
  }

  private castDamageSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, endPosition, id } = spellVisual

    if (spell.name.toLowerCase().includes('fireball')) {
      this.createFireballSpell(spellVisual)
    } else if (spell.name.toLowerCase().includes('lightning')) {
      this.createLightningSpell(spellVisual)
    } else if (spell.name.toLowerCase().includes('ice')) {
      this.createIceSpell(spellVisual)
    } else {
      this.createGenericDamageSpell(spellVisual)
    }
  }

  private createFireballSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, endPosition, id, onComplete } = spellVisual

    // Create fireball projectile
    const fireballGeometry = new THREE.SphereGeometry(0.5)
    const fireballMaterial = new THREE.MeshBasicMaterial({
      color: 0xff6600,
      emissive: 0xff3300,
      emissiveIntensity: 1
    })
    const fireball = new THREE.Mesh(fireballGeometry, fireballMaterial)
    fireball.position.copy(startPosition)

    // Add fire particles
    const fireParticles = new FireballEffect(startPosition)
    fireParticles.start()

    // Add glow effect
    const glowGeometry = new THREE.SphereGeometry(0.8)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: 0xffaa00,
      transparent: true,
      opacity: 0.3
    })
    const glow = new THREE.Mesh(glowGeometry, glowMaterial)
    fireball.add(glow)

    this.scene.add(fireball)
    this.scene.add(fireParticles.emitter)
    this.meshes.set(`${id}_projectile`, fireball)
    this.particleSystems.set(`${id}_particles`, fireParticles)

    // Animate fireball movement
    const duration = spell.speed || 1
    const timeline = gsap.timeline()

    timeline.to(fireball.position, {
      x: endPosition!.x,
      y: endPosition!.y,
      z: endPosition!.z,
      duration: duration,
      ease: "power2.inOut",
      onUpdate: () => {
        fireParticles.emitter.position.copy(fireball.position)
      }
    })

    timeline.call(() => {
      // Create explosion at target
      this.createExplosion(endPosition!, spell.damage || 0)

      // Remove fireball
      this.cleanupSpell(id)

      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private createLightningSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, endPosition, id, onComplete } = spellVisual

    // Create lightning bolt
    const lightning = this.createLightningBolt(startPosition, endPosition!)

    // Add lightning particles
    const lightningParticles = new LightningEffect(startPosition)
    lightningParticles.start()

    // Add electric arc effect
    const arcMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.8
    })

    this.scene.add(lightning)
    this.scene.add(lightningParticles.emitter)
    this.meshes.set(`${id}_lightning`, lightning)
    this.particleSystems.set(`${id}_particles`, lightningParticles)

    // Animate lightning
    const timeline = gsap.timeline()

    // Flash effect
    lightning.material = arcMaterial
    timeline.to(lightning.material, {
      opacity: 1,
      duration: 0.1
    })

    timeline.to(lightning.material, {
      opacity: 0,
      duration: 0.4,
      ease: "power2.out"
    })

    // Chain lightning effect if multiple targets
    if (spell.radius && spell.radius > 5) {
      this.createChainLightning(endPosition!, spell.radius)
    }

    timeline.call(() => {
      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private createIceSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, endPosition, id, onComplete } = spellVisual

    // Create ice shard projectile
    const iceGeometry = new THREE.OctahedronGeometry(0.4)
    const iceMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.8,
      emissive: 0x0088ff,
      emissiveIntensity: 0.5
    })
    const iceShard = new THREE.Mesh(iceGeometry, iceMaterial)
    iceShard.position.copy(startPosition)

    // Add ice particles
    const iceParticles = new ParticleSystem({
      type: 'ice' as any,
      count: 30,
      lifespan: 1.5,
      speed: 2,
      size: 0.2,
      colors: [0x00ffff, 0x0088ff, 0xffffff],
      gravity: 0,
      spread: 0.5
    }, startPosition)
    iceParticles.start()

    this.scene.add(iceShard)
    this.scene.add(iceParticles.emitter)
    this.meshes.set(`${id}_projectile`, iceShard)
    this.particleSystems.set(`${id}_particles`, iceParticles)

    // Animate ice shard
    const duration = spell.speed || 0.8
    const timeline = gsap.timeline()

    // Add spinning effect
    gsap.to(iceShard.rotation, {
      x: Math.PI * 4,
      y: Math.PI * 2,
      duration: duration,
      ease: "none"
    })

    timeline.to(iceShard.position, {
      x: endPosition!.x,
      y: endPosition!.y,
      z: endPosition!.z,
      duration: duration,
      ease: "power2.inOut",
      onUpdate: () => {
        iceParticles.emitter.position.copy(iceShard.position)
      }
    })

    timeline.call(() => {
      // Create ice explosion
      this.createIceExplosion(endPosition!)

      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private createGenericDamageSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, endPosition, id, onComplete } = spellVisual

    // Create energy projectile
    const energyGeometry = new THREE.SphereGeometry(0.3)
    const energyMaterial = new THREE.MeshBasicMaterial({
      color: spell.color || 0xff00ff,
      transparent: true,
      opacity: 0.8
    })
    const energy = new THREE.Mesh(energyGeometry, energyMaterial)
    energy.position.copy(startPosition)

    // Add energy particles
    const energyParticles = new ParticleSystem({
      type: 'magic' as any,
      count: 25,
      lifespan: 1,
      speed: 3,
      size: 0.2,
      color: spell.color || 0xff00ff,
      gravity: 0,
      spread: 0.3
    }, startPosition)
    energyParticles.start()

    this.scene.add(energy)
    this.scene.add(energyParticles.emitter)
    this.meshes.set(`${id}_projectile`, energy)
    this.particleSystems.set(`${id}_particles`, energyParticles)

    // Animate energy projectile
    const duration = spell.speed || 1
    const timeline = gsap.timeline()

    timeline.to(energy.position, {
      x: endPosition!.x,
      y: endPosition!.y,
      z: endPosition!.z,
      duration: duration,
      ease: "power2.inOut",
      onUpdate: () => {
        energyParticles.emitter.position.copy(energy.position)
      }
    })

    timeline.call(() => {
      // Create impact effect
      this.createImpactEffect(endPosition!, spell.color || 0xff00ff)

      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private castHealingSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, target, id, onComplete } = spellVisual

    if (!target) return

    // Create healing effect around target
    const healingParticles = new HealingEffect(target.position)
    healingParticles.start()

    // Create healing aura
    const auraGeometry = new THREE.RingGeometry(1, 2, 32)
    const auraMaterial = new THREE.MeshBasicMaterial({
      color: 0xffd700,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    })
    const aura = new THREE.Mesh(auraGeometry, auraMaterial)
    aura.position.copy(target.position)
    aura.rotation.x = -Math.PI / 2

    // Create rising light particles
    const lightParticles = []
    for (let i = 0; i < 20; i++) {
      const particleGeometry = new THREE.SphereGeometry(0.05)
      const particleMaterial = new THREE.MeshBasicMaterial({
        color: 0xffed4e,
        emissive: 0xffd700,
        emissiveIntensity: 1
      })
      const particle = new THREE.Mesh(particleGeometry, particleMaterial)

      const angle = (i / 20) * Math.PI * 2
      const radius = 1.5
      particle.position.set(
        target.position.x + Math.cos(angle) * radius,
        target.position.y,
        target.position.z + Math.sin(angle) * radius
      )

      this.scene.add(particle)
      lightParticles.push(particle)
    }

    this.scene.add(healingParticles.emitter)
    this.scene.add(aura)
    this.particleSystems.set(`${id}_particles`, healingParticles)
    this.meshes.set(`${id}_aura`, aura)
    lightParticles.forEach((particle, i) => {
      this.meshes.set(`${id}_light_${i}`, particle)
    })

    // Animate healing effect
    const timeline = gsap.timeline()

    // Animate aura expansion and fade
    timeline.to(aura.scale, {
      x: 2,
      y: 2,
      z: 2,
      duration: spell.castTime || 1,
      ease: "power2.out"
    })

    timeline.to(aura.material, {
      opacity: 0,
      duration: 0.5,
      ease: "power2.in"
    }, "-=0.5")

    // Animate light particles rising
    lightParticles.forEach((particle, i) => {
      const delay = i * 0.05
      timeline.to(particle.position, {
        y: target.position.y + 3,
        opacity: 0,
        duration: 1.5,
        ease: "power2.out",
        onStart: () => {
          this.scene.add(particle)
        }
      }, delay)
    })

    // Floating healing numbers would be handled by the combat feedback system

    timeline.call(() => {
      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private castBuffSpell(spellVisual: SpellVisual): void {
    const { spell, target, id, onComplete } = spellVisual

    if (!target) return

    // Create buff aura
    const buffGeometry = new THREE.TorusGeometry(1.2, 0.2, 16, 32)
    const buffMaterial = new THREE.MeshBasicMaterial({
      color: spell.color || 0x00ff00,
      transparent: true,
      opacity: 0.6
    })
    const buffAura = new THREE.Mesh(buffGeometry, buffMaterial)
    buffAura.position.copy(target.position)

    // Add buff particles
    const buffParticles = new ParticleSystem({
      type: 'magic' as any,
      count: 30,
      lifespan: 2,
      speed: 1,
      size: 0.15,
      color: spell.color || 0x00ff00,
      gravity: 0,
      spread: 2
    }, target.position)
    buffParticles.start()

    this.scene.add(buffAura)
    this.scene.add(buffParticles.emitter)
    this.meshes.set(`${id}_aura`, buffAura)
    this.particleSystems.set(`${id}_particles`, buffParticles)

    // Animate buff effect
    const timeline = gsap.timeline()

    // Rotate buff aura
    gsap.to(buffAura.rotation, {
      x: Math.PI * 2,
      y: Math.PI * 2,
      duration: 3,
      repeat: -1,
      ease: "none"
    })

    // Pulsing effect
    timeline.to(buffAura.material, {
      opacity: 0.9,
      duration: 0.5,
      yoyo: true,
      repeat: 3
    })

    timeline.call(() => {
      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private castDebuffSpell(spellVisual: SpellVisual): void {
    const { spell, target, id, onComplete } = spellVisual

    if (!target) return

    // Create debuff effect
    const debuffGeometry = new THREE.OctahedronGeometry(0.8)
    const debuffMaterial = new THREE.MeshBasicMaterial({
      color: spell.color || 0x800080,
      transparent: true,
      opacity: 0.7,
      wireframe: true
    })
    const debuffOrb = new THREE.Mesh(debuffGeometry, debuffMaterial)
    debuffOrb.position.copy(target.position)

    this.scene.add(debuffOrb)
    this.meshes.set(`${id}_orb`, debuffOrb)

    // Animate debuff effect
    const timeline = gsap.timeline()

    // Shrinking and fading effect
    timeline.to(debuffOrb.scale, {
      x: 0.1,
      y: 0.1,
      z: 0.1,
      duration: spell.castTime || 1,
      ease: "power2.in"
    })

    timeline.to(debuffOrb.material, {
      opacity: 0,
      duration: 0.5,
      ease: "power2.in"
    }, "-=0.5")

    timeline.call(() => {
      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private castIllusionSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, endPosition, id, onComplete } = spellVisual

    // Create shimmering illusion effect
    const illusionGeometry = new THREE.PlaneGeometry(2, 2)
    const illusionMaterial = new THREE.MeshBasicMaterial({
      color: spell.color || 0xff00ff,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    })
    const illusion = new THREE.Mesh(illusionGeometry, illusionMaterial)
    illusion.position.copy(endPosition || startPosition)

    // Add shimmer particles
    const shimmerParticles = new ParticleSystem({
      type: 'magic' as any,
      count: 40,
      lifespan: 3,
      speed: 0.5,
      size: 0.1,
      colors: [0xff00ff, 0x00ffff, 0xffffff],
      gravity: 0,
      spread: 3
    }, illusion.position)
    shimmerParticles.start()

    this.scene.add(illusion)
    this.scene.add(shimmerParticles.emitter)
    this.meshes.set(`${id}_illusion`, illusion)
    this.particleSystems.set(`${id}_particles`, shimmerParticles)

    // Animate illusion
    const timeline = gsap.timeline()

    // Wobbling effect
    timeline.to(illusion.rotation, {
      x: Math.PI / 6,
      duration: 1,
      ease: "sine.inOut",
      yoyo: true,
      repeat: 3
    })

    timeline.to(illusion.material, {
      opacity: 0.8,
      duration: 0.5,
      yoyo: true,
      repeat: 3
    }, 0)

    timeline.call(() => {
      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private castSummoningSpell(spellVisual: SpellVisual): void {
    const { spell, startPosition, id, onComplete } = spellVisual

    // Create summoning portal
    const portalGeometry = new THREE.RingGeometry(0.5, 2, 32)
    const portalMaterial = new THREE.MeshBasicMaterial({
      color: spell.color || 0x800080,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    })
    const portal = new THREE.Mesh(portalGeometry, portalMaterial)
    portal.position.copy(startPosition)
    portal.rotation.x = -Math.PI / 2

    // Add portal particles
    const portalParticles = new ParticleSystem({
      type: 'magic' as any,
      count: 60,
      lifespan: 2,
      speed: 2,
      size: 0.2,
      colors: [0x800080, 0xff00ff, 0x0000ff],
      gravity: 0,
      spread: 2
    }, startPosition)
    portalParticles.start()

    this.scene.add(portal)
    this.scene.add(portalParticles.emitter)
    this.meshes.set(`${id}_portal`, portal)
    this.particleSystems.set(`${id}_particles`, portalParticles)

    // Animate portal
    const timeline = gsap.timeline()

    // Portal expansion
    timeline.from(portal.scale, {
      x: 0,
      y: 0,
      z: 0,
      duration: 1,
      ease: "back.out(1.7)"
    })

    // Spinning effect
    gsap.to(portal.rotation, {
      z: Math.PI * 4,
      duration: 4,
      ease: "none"
    })

    // Pulsing effect
    timeline.to(portal.material, {
      opacity: 1,
      duration: 0.5,
      yoyo: true,
      repeat: 3
    })

    timeline.call(() => {
      this.cleanupSpell(id)
      if (onComplete) onComplete()
    })

    this.timelines.set(id, timeline)
  }

  private createLightningBolt(start: THREE.Vector3, end: THREE.Vector3): THREE.Line {
    const points = this.generateLightningPath(start, end)
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({
      color: 0x00ffff,
      linewidth: 3
    })

    return new THREE.Line(geometry, material)
  }

  private generateLightningPath(start: THREE.Vector3, end: THREE.Vector3): THREE.Vector3[] {
    const points: THREE.Vector3[] = [start.clone()]
    const segments = 8
    const offset = 0.5

    for (let i = 1; i < segments; i++) {
      const t = i / segments
      const point = new THREE.Vector3().lerpVectors(start, end, t)

      // Add random offset for lightning effect
      point.x += (Math.random() - 0.5) * offset
      point.y += (Math.random() - 0.5) * offset
      point.z += (Math.random() - 0.5) * offset

      points.push(point)
    }

    points.push(end.clone())
    return points
  }

  private createChainLightning(origin: THREE.Vector3, radius: number): void {
    const numChains = 3
    for (let i = 0; i < numChains; i++) {
      const angle = (i / numChains) * Math.PI * 2
      const target = new THREE.Vector3(
        origin.x + Math.cos(angle) * radius,
        origin.y + (Math.random() - 0.5) * 2,
        origin.z + Math.sin(angle) * radius
      )

      const chainBolt = this.createLightningBolt(origin, target)
      const chainMaterial = chainBolt.material as THREE.LineBasicMaterial
      chainMaterial.opacity = 0.6

      this.scene.add(chainBolt)

      // Fade out chain lightning
      gsap.to(chainMaterial, {
        opacity: 0,
        duration: 0.3,
        ease: "power2.out",
        onComplete: () => {
          this.scene.remove(chainBolt)
        }
      })
    }
  }

  private createExplosion(position: THREE.Vector3, damage: number): void {
    const explosion = new ExplosionEffect(position)
    explosion.start()
    this.scene.add(explosion.emitter)

    // Auto-cleanup after explosion
    setTimeout(() => {
      this.scene.remove(explosion.emitter)
      explosion.dispose()
    }, 2000)

    // Create shockwave
    this.createShockwave(position, damage)
  }

  private createIceExplosion(position: THREE.Vector3): void {
    // Create ice shards explosion
    const numShards = 20
    for (let i = 0; i < numShards; i++) {
      const shardGeometry = new THREE.OctahedronGeometry(0.1 + Math.random() * 0.2)
      const shardMaterial = new THREE.MeshBasicMaterial({
        color: 0x00ffff,
        transparent: true,
        opacity: 0.8
      })
      const shard = new THREE.Mesh(shardGeometry, shardMaterial)
      shard.position.copy(position)

      this.scene.add(shard)

      // Animate shard
      const direction = new THREE.Vector3(
        (Math.random() - 0.5) * 10,
        Math.random() * 5,
        (Math.random() - 0.5) * 10
      )

      gsap.to(shard.position, {
        x: position.x + direction.x,
        y: position.y + direction.y,
        z: position.z + direction.z,
        duration: 1,
        ease: "power2.out"
      })

      gsap.to(shard.material, {
        opacity: 0,
        duration: 1,
        ease: "power2.in",
        onComplete: () => {
          this.scene.remove(shard)
        }
      })

      gsap.to(shard.rotation, {
        x: Math.random() * Math.PI * 4,
        y: Math.random() * Math.PI * 4,
        z: Math.random() * Math.PI * 4,
        duration: 1,
        ease: "none"
      })
    }

    // Add ice particles
    const iceParticles = new ParticleSystem({
      type: 'ice' as any,
      count: 40,
      lifespan: 2,
      speed: 3,
      size: 0.2,
      colors: [0x00ffff, 0x0088ff, 0xffffff],
      gravity: -2,
      spread: 3
    }, position)
    iceParticles.start()
    this.scene.add(iceParticles.emitter)

    setTimeout(() => {
      this.scene.remove(iceParticles.emitter)
      iceParticles.dispose()
    }, 2000)
  }

  private createImpactEffect(position: THREE.Vector3, color: number): void {
    const impactParticles = new ParticleSystem({
      type: 'magic' as any,
      count: 30,
      lifespan: 1,
      speed: 4,
      size: 0.3,
      color: color,
      gravity: 0,
      spread: 2
    }, position)
    impactParticles.start()
    this.scene.add(impactParticles.emitter)

    setTimeout(() => {
      this.scene.remove(impactParticles.emitter)
      impactParticles.dispose()
    }, 1500)
  }

  private createShockwave(position: THREE.Vector3, damage: number): void {
    const shockwaveGeometry = new THREE.RingGeometry(0.1, 0.5, 32)
    const shockwaveMaterial = new THREE.MeshBasicMaterial({
      color: 0xff6600,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    })
    const shockwave = new THREE.Mesh(shockwaveGeometry, shockwaveMaterial)
    shockwave.position.copy(position)
    shockwave.rotation.x = -Math.PI / 2

    this.scene.add(shockwave)

    // Animate shockwave
    gsap.to(shockwave.scale, {
      x: damage / 10,
      y: damage / 10,
      z: damage / 10,
      duration: 0.5,
      ease: "power2.out"
    })

    gsap.to(shockwave.material, {
      opacity: 0,
      duration: 0.5,
      ease: "power2.in",
      onComplete: () => {
        this.scene.remove(shockwave)
      }
    })
  }

  private cleanupSpell(spellId: string): void {
    // Remove meshes
    this.meshes.forEach((mesh, key) => {
      if (key.startsWith(spellId)) {
        this.scene.remove(mesh)
        if (mesh instanceof THREE.Mesh) {
          mesh.geometry.dispose()
          if (mesh.material instanceof THREE.Material) {
            mesh.material.dispose()
          }
        }
        this.meshes.delete(key)
      }
    })

    // Remove particle systems
    this.particleSystems.forEach((system, key) => {
      if (key.startsWith(spellId)) {
        this.scene.remove(system.emitter)
        system.dispose()
        this.particleSystems.delete(key)
      }
    })

    // Kill timelines
    this.timelines.forEach((timeline, key) => {
      if (key.startsWith(spellId)) {
        timeline.kill()
        this.timelines.delete(key)
      }
    })

    // Remove from active spells
    this.activeSpells.delete(spellId)
  }

  public update(deltaTime: number): void {
    // Update all particle systems
    this.particleSystems.forEach(system => {
      system.update(deltaTime)
    })
  }

  public dispose(): void {
    // Cleanup all active spells
    const spellIds = Array.from(this.activeSpells.keys())
    spellIds.forEach(id => this.cleanupSpell(id))
  }
}