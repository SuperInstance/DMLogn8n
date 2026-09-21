import * as THREE from 'three'
import { ParticleEffectConfig, ParticleType } from '@/types'

export interface Particle {
  position: THREE.Vector3
  velocity: THREE.Vector3
  acceleration: THREE.Vector3
  life: number
  maxLife: number
  size: number
  color: THREE.Color
  opacity: number
  rotation: THREE.Vector3
  rotationSpeed: THREE.Vector3
  scale: THREE.Vector3
}

export class ParticleSystem {
  public particles: Particle[] = []
  public particleMesh?: THREE.Points
  public emitter: THREE.Object3D
  public config: ParticleEffectConfig

  private geometry: THREE.BufferGeometry
  private positions: Float32Array
  private colors: Float32Array
  private sizes: Float32Array
  private opacities: Float32Array
  private rotations: Float32Array
  private material: THREE.PointsMaterial

  private active: boolean = false
  private elapsedTime: number = 0
  private emissionRate: number = 0
  private emissionAccumulator: number = 0

  constructor(config: ParticleEffectConfig, position: THREE.Vector3) {
    this.config = config
    this.emitter = new THREE.Object3D()
    this.emitter.position.copy(position)

    this.geometry = new THREE.BufferGeometry()
    this.material = this.createMaterial()

    this.initBuffers()
    this.createParticleMesh()
    this.calculateEmissionRate()
  }

  private createMaterial(): THREE.PointsMaterial {
    const material = new THREE.PointsMaterial({
      size: this.config.size,
      vertexColors: true,
      transparent: true,
      opacity: 1,
      blending: this.getBlendingMode(),
      depthWrite: false,
      sizeAttenuation: true
    })

    // Set texture if provided
    if (this.config.texture) {
      const textureLoader = new THREE.TextureLoader()
      textureLoader.load(this.config.texture, (texture) => {
        material.map = texture
        material.needsUpdate = true
      })
    }

    return material
  }

  private getBlendingMode(): THREE.Blending {
    switch (this.config.type) {
      case ParticleType.Fire:
      case ParticleType.Lightning:
      case ParticleType.Magic:
        return THREE.AdditiveBlending
      case ParticleType.Healing:
        return THREE.AdditiveBlending
      case ParticleType.Ice:
      case ParticleType.Smoke:
        return THREE.NormalBlending
      default:
        return THREE.NormalBlending
    }
  }

  private initBuffers(): void {
    const maxParticles = this.config.count
    this.positions = new Float32Array(maxParticles * 3)
    this.colors = new Float32Array(maxParticles * 3)
    this.sizes = new Float32Array(maxParticles)
    this.opacities = new Float32Array(maxParticles)
    this.rotations = new Float32Array(maxParticles * 3)

    this.geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3))
    this.geometry.setAttribute('color', new THREE.BufferAttribute(this.colors, 3))
    this.geometry.setAttribute('size', new THREE.BufferAttribute(this.sizes, 1))
    this.geometry.setAttribute('opacity', new THREE.BufferAttribute(this.opacities, 1))
    this.geometry.setAttribute('rotation', new THREE.BufferAttribute(this.rotations, 3))
  }

  private createParticleMesh(): void {
    this.particleMesh = new THREE.Points(this.geometry, this.material)
    this.particleMesh.frustumCulled = false
    this.emitter.add(this.particleMesh)
  }

  private calculateEmissionRate(): void {
    this.emissionRate = this.config.count / this.config.lifespan
  }

  public start(): void {
    this.active = true
    this.elapsedTime = 0
  }

  public stop(): void {
    this.active = false
  }

  public update(deltaTime: number): void {
    if (!this.active && this.particles.length === 0) return

    this.elapsedTime += deltaTime

    // Emit new particles
    if (this.active) {
      this.emitParticles(deltaTime)
    }

    // Update existing particles
    this.updateParticles(deltaTime)
    this.updateBuffers()

    // Remove dead particles
    this.removeDeadParticles()

    // Auto-stop when all particles are dead and not emitting
    if (!this.active && this.particles.length === 0) {
      this.stop()
    }
  }

  private emitParticles(deltaTime: number): void {
    this.emissionAccumulator += this.emissionRate * deltaTime

    while (this.emissionAccumulator >= 1 && this.particles.length < this.config.count) {
      this.createParticle()
      this.emissionAccumulator -= 1
    }
  }

  private createParticle(): void {
    const particle: Particle = {
      position: this.getInitialPosition(),
      velocity: this.getInitialVelocity(),
      acceleration: new THREE.Vector3(
        0,
        this.config.gravity || 0,
        0
      ),
      life: 0,
      maxLife: this.config.lifespan + (Math.random() - 0.5) * this.config.lifespan * 0.5,
      size: this.config.size + (Math.random() - 0.5) * this.config.size * 0.5,
      color: this.getParticleColor(),
      opacity: 1,
      rotation: new THREE.Vector3(
        Math.random() * Math.PI * 2,
        Math.random() * Math.PI * 2,
        Math.random() * Math.PI * 2
      ),
      rotationSpeed: new THREE.Vector3(
        (Math.random() - 0.5) * 2,
        (Math.random() - 0.5) * 2,
        (Math.random() - 0.5) * 2
      ),
      scale: new THREE.Vector3(1, 1, 1)
    }

    this.particles.push(particle)
  }

  private getInitialPosition(): THREE.Vector3 {
    const spread = this.config.spread || 1
    return new THREE.Vector3(
      (Math.random() - 0.5) * spread,
      (Math.random() - 0.5) * spread,
      (Math.random() - 0.5) * spread
    )
  }

  private getInitialVelocity(): THREE.Vector3 {
    const spread = this.config.spread || 1
    const speed = this.config.speed

    let velocity = new THREE.Vector3(
      (Math.random() - 0.5) * spread,
      Math.random() * speed,
      (Math.random() - 0.5) * spread
    )

    // Apply specific patterns based on particle type
    switch (this.config.type) {
      case ParticleType.Fire:
        velocity.y = Math.random() * speed
        velocity.x = (Math.random() - 0.5) * speed * 0.5
        velocity.z = (Math.random() - 0.5) * speed * 0.5
        break

      case ParticleType.Lightning:
        velocity = new THREE.Vector3(
          (Math.random() - 0.5) * speed * 0.1,
          0,
          Math.random() * speed
        )
        break

      case ParticleType.Healing:
        velocity.y = Math.random() * speed * 0.3
        velocity.x = (Math.random() - 0.5) * speed * 0.5
        velocity.z = (Math.random() - 0.5) * speed * 0.5
        break

      case ParticleType.Ice:
        velocity.y = Math.random() * speed * 0.2
        velocity.x = (Math.random() - 0.5) * speed * 0.8
        velocity.z = (Math.random() - 0.5) * speed * 0.8
        break

      case ParticleType.Explosion:
        velocity = new THREE.Vector3(
          (Math.random() - 0.5) * speed * 2,
          Math.random() * speed * 1.5,
          (Math.random() - 0.5) * speed * 2
        )
        break
    }

    return velocity
  }

  private getParticleColor(): THREE.Color {
    if (this.config.colors && this.config.colors.length > 0) {
      const colorIndex = Math.floor(Math.random() * this.config.colors.length)
      return new THREE.Color(this.config.colors[colorIndex])
    }

    if (this.config.color !== undefined) {
      return new THREE.Color(this.config.color)
    }

    // Default colors based on particle type
    switch (this.config.type) {
      case ParticleType.Fire:
        return new THREE.Color(0xff6600)
      case ParticleType.Lightning:
        return new THREE.Color(0x00ffff)
      case ParticleType.Healing:
        return new THREE.Color(0xffd700)
      case ParticleType.Ice:
        return new THREE.Color(0x00ffff)
      case ParticleType.Earth:
        return new THREE.Color(0x8b4513)
      case ParticleType.Wind:
        return new THREE.Color(0xffffff)
      case ParticleType.Blood:
        return new THREE.Color(0xff0000)
      case ParticleType.Magic:
        return new THREE.Color(0xff00ff)
      case ParticleType.Smoke:
        return new THREE.Color(0x333333)
      case ParticleType.Explosion:
        return new THREE.Color(0xffaa00)
      default:
        return new THREE.Color(0xffffff)
    }
  }

  private updateParticles(deltaTime: number): void {
    for (const particle of this.particles) {
      // Update life
      particle.life += deltaTime

      // Update physics
      particle.velocity.add(particle.acceleration.clone().multiplyScalar(deltaTime))
      particle.position.add(particle.velocity.clone().multiplyScalar(deltaTime))

      // Update rotation
      particle.rotation.add(particle.rotationSpeed.clone().multiplyScalar(deltaTime))

      // Update opacity based on life
      const lifeRatio = particle.life / particle.maxLife
      particle.opacity = Math.max(0, 1 - lifeRatio)

      // Update size based on particle type
      this.updateParticleSize(particle, lifeRatio)

      // Update color based on particle type
      this.updateParticleColor(particle, lifeRatio)
    }
  }

  private updateParticleSize(particle: Particle, lifeRatio: number): void {
    switch (this.config.type) {
      case ParticleType.Fire:
        particle.scale.setScalar(1 + lifeRatio * 0.5)
        break

      case ParticleType.Smoke:
        particle.scale.setScalar(1 + lifeRatio * 2)
        break

      case ParticleType.Explosion:
        particle.scale.setScalar(1 + lifeRatio * 3)
        break

      case ParticleType.Healing:
        particle.scale.setScalar(1 + Math.sin(lifeRatio * Math.PI * 4) * 0.2)
        break

      default:
        particle.scale.setScalar(1)
        break
    }
  }

  private updateParticleColor(particle: Particle, lifeRatio: number): void {
    switch (this.config.type) {
      case ParticleType.Fire:
        const fireColor = new THREE.Color()
        fireColor.setHSL(0.08, 1, 1 - lifeRatio * 0.5)
        particle.color = fireColor
        break

      case ParticleType.Lightning:
        const lightningColor = new THREE.Color(0x00ffff)
        lightningColor.multiplyScalar(1 - lifeRatio * 0.5)
        particle.color = lightningColor
        break

      case ParticleType.Healing:
        const healingColor = new THREE.Color()
        healingColor.setHSL(0.15, 1, 0.5 + lifeRatio * 0.3)
        particle.color = healingColor
        break

      case ParticleType.Blood:
        const bloodColor = new THREE.Color(0xff0000)
        bloodColor.r *= 1 - lifeRatio * 0.3
        bloodColor.g *= 1 - lifeRatio * 0.5
        particle.color = bloodColor
        break

      case ParticleType.Smoke:
        const smokeColor = new THREE.Color(0x333333)
        smokeColor.lerp(new THREE.Color(0x999999), lifeRatio)
        particle.color = smokeColor
        break

      default:
        // Keep original color
        break
    }
  }

  private updateBuffers(): void {
    for (let i = 0; i < this.particles.length; i++) {
      const particle = this.particles[i]
      const i3 = i * 3

      // Position
      this.positions[i3] = particle.position.x
      this.positions[i3 + 1] = particle.position.y
      this.positions[i3 + 2] = particle.position.z

      // Color
      this.colors[i3] = particle.color.r
      this.colors[i3 + 1] = particle.color.g
      this.colors[i3 + 2] = particle.color.b

      // Size
      this.sizes[i] = particle.size * particle.scale.x

      // Opacity
      this.opacities[i] = particle.opacity

      // Rotation
      this.rotations[i3] = particle.rotation.x
      this.rotations[i3 + 1] = particle.rotation.y
      this.rotations[i3 + 2] = particle.rotation.z
    }

    this.geometry.attributes.position.needsUpdate = true
    this.geometry.attributes.color.needsUpdate = true
    this.geometry.attributes.size.needsUpdate = true
    this.geometry.attributes.opacity.needsUpdate = true
    this.geometry.attributes.rotation.needsUpdate = true

    // Hide unused particles
    for (let i = this.particles.length; i < this.config.count; i++) {
      this.opacities[i] = 0
    }
    this.geometry.attributes.opacity.needsUpdate = true
  }

  private removeDeadParticles(): void {
    this.particles = this.particles.filter(particle => particle.life < particle.maxLife)
  }

  public setPosition(position: THREE.Vector3): void {
    this.emitter.position.copy(position)
  }

  public setEmissionDirection(direction: THREE.Vector3): void {
    // This would affect initial velocity calculation
    // Implementation depends on specific requirements
  }

  public isAlive(): boolean {
    return this.active || this.particles.length > 0
  }

  public dispose(): void {
    if (this.particleMesh) {
      this.emitter.remove(this.particleMesh)
      this.particleMesh.geometry.dispose()
      if (this.particleMesh.material instanceof THREE.Material) {
        this.particleMesh.material.dispose()
      }
    }

    this.geometry.dispose()
    this.material.dispose()
    this.particles = []
  }
}

// Specialized particle systems for specific effects
export class FireballEffect extends ParticleSystem {
  constructor(position: THREE.Vector3) {
    super({
      type: ParticleType.Fire,
      count: 50,
      lifespan: 2,
      speed: 3,
      size: 0.3,
      colors: [0xff6600, 0xff9900, 0xffcc00],
      gravity: -0.5,
      spread: 0.5,
      rotation: new THREE.Vector3(0, 0, 0)
    }, position)

    this.emissionRate = 25 // Higher emission rate for continuous fire
  }
}

export class LightningEffect extends ParticleSystem {
  constructor(position: THREE.Vector3) {
    super({
      type: ParticleType.Lightning,
      count: 30,
      lifespan: 0.5,
      speed: 20,
      size: 0.2,
      color: 0x00ffff,
      gravity: 0,
      spread: 0.2,
      rotation: new THREE.Vector3(0, 0, 0)
    }, position)

    this.emissionRate = 60 // Very fast emission for lightning
  }
}

export class HealingEffect extends ParticleSystem {
  constructor(position: THREE.Vector3) {
    super({
      type: ParticleType.Healing,
      count: 40,
      lifespan: 3,
      speed: 1,
      size: 0.4,
      colors: [0xffd700, 0xffed4e, 0xffffff],
      gravity: -0.2,
      spread: 1,
      rotation: new THREE.Vector3(0, 0, 0)
    }, position)

    this.emissionRate = 15
  }
}

export class ExplosionEffect extends ParticleSystem {
  constructor(position: THREE.Vector3) {
    super({
      type: ParticleType.Explosion,
      count: 100,
      lifespan: 1.5,
      speed: 8,
      size: 0.5,
      colors: [0xff6600, 0xffaa00, 0xffff00, 0xff0000],
      gravity: -2,
      spread: 2,
      rotation: new THREE.Vector3(0, 0, 0)
    }, position)

    this.emissionRate = 100 // Emit all particles at once
  }
}

export class BloodEffect extends ParticleSystem {
  constructor(position: THREE.Vector3) {
    super({
      type: ParticleType.Blood,
      count: 20,
      lifespan: 2,
      speed: 2,
      size: 0.15,
      color: 0xff0000,
      gravity: -5,
      spread: 0.8,
      rotation: new THREE.Vector3(0, 0, 0)
    }, position)

    this.emissionRate = 20
  }
}