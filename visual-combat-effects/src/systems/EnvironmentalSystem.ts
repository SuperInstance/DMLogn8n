import * as THREE from 'three'
import { EnvironmentObject, EnvironmentType, WeatherConfig, WeatherType } from '@/types'
import { ParticleSystem, ParticleType } from '@/effects/ParticleSystem'

export class EnvironmentalSystem {
  private scene: THREE.Scene
  private environmentObjects: Map<string, EnvironmentObject> = new Map()
  private weatherParticles?: ParticleSystem
  private timeOfDay: number = 12 // 24-hour format
  private dayNightCycleSpeed: number = 0.1 // Hours per second
  private ambientLight?: THREE.AmbientLight
  private directionalLight?: THREE.DirectionalLight
  private fog?: THREE.Fog

  constructor(scene: THREE.Scene) {
    this.scene = scene
    this.setupLighting()
    this.setupFog()
  }

  private setupLighting(): void {
    // Store references to lights for day/night cycle
    this.scene.traverse((object) => {
      if (object instanceof THREE.AmbientLight) {
        this.ambientLight = object
      } else if (object instanceof THREE.DirectionalLight) {
        this.directionalLight = object
      }
    })
  }

  private setupFog(): void {
    if (this.scene.fog) {
      this.fog = this.scene.fog
    }
  }

  public addEnvironmentObject(envObject: EnvironmentObject): void {
    this.environmentObjects.set(envObject.id, envObject)
    if (envObject.mesh) {
      this.scene.add(envObject.mesh)
    }
  }

  public removeEnvironmentObject(id: string): void {
    const envObject = this.environmentObjects.get(id)
    if (envObject && envObject.mesh) {
      this.scene.remove(envObject.mesh)
      this.environmentObjects.delete(id)
    }
  }

  public damageEnvironmentObject(id: string, damage: number): boolean {
    const envObject = this.environmentObjects.get(id)
    if (!envObject || !envObject.destructible || !envObject.health) {
      return false
    }

    envObject.health -= damage

    // Visual feedback for damage
    this.createDamageEffect(envObject, damage)

    if (envObject.health <= 0) {
      this.destroyEnvironmentObject(envObject)
      return true
    }

    return false
  }

  private createDamageEffect(envObject: EnvironmentObject, damage: number): void {
    if (!envObject.mesh) return

    // Flash effect
    const originalMaterials: THREE.Material[] = []
    envObject.mesh.traverse((child) => {
      if (child instanceof THREE.Mesh && child.material instanceof THREE.MeshStandardMaterial) {
        originalMaterials.push(child.material)
        const damageMaterial = child.material.clone()
        damageMaterial.emissive = new THREE.Color(0xff0000)
        damageMaterial.emissiveIntensity = 0.5
        child.material = damageMaterial
      }
    })

    // Restore original materials after flash
    setTimeout(() => {
      envObject.mesh!.traverse((child, index) => {
        if (child instanceof THREE.Mesh && originalMaterials[index]) {
          child.material = originalMaterials[index]
        }
      })
    }, 100)

    // Create damage particles
    this.createDebrisParticles(envObject.mesh.position, envObject.type)

    // Shake effect for destructible objects
    if (envObject.destructible) {
      this.shakeObject(envObject.mesh, damage / 50)
    }
  }

  private createDebrisParticles(position: THREE.Vector3, objectType: EnvironmentType): void {
    let particleConfig: any

    switch (objectType) {
      case EnvironmentType.Barrel:
      case EnvironmentType.Crate:
        particleConfig = {
          type: ParticleType.Earth,
          count: 15,
          lifespan: 1.5,
          speed: 3,
          size: 0.1,
          colors: [0x8b4513, 0x654321, 0x4a2c17],
          gravity: -9.8,
          spread: 1
        }
        break
      case EnvironmentType.Pillar:
      case EnvironmentType.Wall:
      case EnvironmentType.Rock:
        particleConfig = {
          type: ParticleType.Earth,
          count: 20,
          lifespan: 2,
          speed: 4,
          size: 0.15,
          colors: [0x808080, 0x696969, 0xa9a9a9],
          gravity: -9.8,
          spread: 1.5
        }
        break
      case EnvironmentType.Tree:
        particleConfig = {
          type: ParticleType.Earth,
          count: 25,
          lifespan: 2.5,
          speed: 5,
          size: 0.2,
          colors: [0x228b22, 0x2e7d32, 0x1b5e20],
          gravity: -5,
          spread: 2
        }
        break
      default:
        particleConfig = {
          type: ParticleType.Earth,
          count: 10,
          lifespan: 1,
          speed: 2,
          size: 0.1,
          color: 0x666666,
          gravity: -9.8,
          spread: 0.8
        }
    }

    const debrisParticles = new ParticleSystem(particleConfig, position)
    debrisParticles.start()
    this.scene.add(debrisParticles.emitter)

    // Auto-cleanup
    setTimeout(() => {
      this.scene.remove(debrisParticles.emitter)
      debrisParticles.dispose()
    }, particleConfig.lifespan * 1000)
  }

  private shakeObject(mesh: THREE.Object3D, intensity: number): void {
    const originalPosition = mesh.position.clone()
    const duration = 0.3

    let startTime: number | null = null
    const shake = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const elapsed = currentTime - startTime
      const progress = elapsed / duration

      if (progress < 1) {
        mesh.position.x = originalPosition.x + (Math.random() - 0.5) * intensity * (1 - progress)
        mesh.position.z = originalPosition.z + (Math.random() - 0.5) * intensity * (1 - progress)
        mesh.position.y = originalPosition.y + (Math.random() - 0.5) * intensity * 0.5 * (1 - progress)
        requestAnimationFrame(shake)
      } else {
        mesh.position.copy(originalPosition)
      }
    }

    requestAnimationFrame(shake)
  }

  private destroyEnvironmentObject(envObject: EnvironmentObject): void {
    if (!envObject.mesh) return

    // Create destruction effect based on object type
    switch (envObject.type) {
      case EnvironmentType.Barrel:
        this.destroyBarrel(envObject.mesh)
        break
      case EnvironmentType.Crate:
        this.destroyCrate(envObject.mesh)
        break
      case EnvironmentType.Tree:
        this.destroyTree(envObject.mesh)
        break
      case EnvironmentType.Pillar:
        this.destroyPillar(envObject.mesh)
        break
      default:
        this.destroyGenericObject(envObject.mesh)
    }

    // Remove from scene
    this.scene.remove(envObject.mesh)
    this.environmentObjects.delete(envObject.id)
  }

  private destroyBarrel(barrel: THREE.Object3D): void {
    // Create barrel pieces
    const pieceGeometry = new THREE.BoxGeometry(0.3, 0.3, 0.3)
    const pieceMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 })

    for (let i = 0; i < 8; i++) {
      const piece = new THREE.Mesh(pieceGeometry, pieceMaterial)
      piece.position.copy(barrel.position)
      piece.position.y += Math.random() * 0.5
      piece.castShadow = true

      this.scene.add(piece)

      // Animate pieces flying apart
      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 5,
        Math.random() * 3 + 2,
        (Math.random() - 0.5) * 5
      )

      this.animateFlyingPiece(piece, velocity, 0.98)
    }

    // Create explosion effect
    this.createDebrisParticles(barrel.position, EnvironmentType.Barrel)
  }

  private destroyCrate(crate: THREE.Object3D): void {
    // Create crate fragments
    const fragmentGeometry = new THREE.BoxGeometry(0.2, 0.4, 0.2)
    const fragmentMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 })

    for (let i = 0; i < 12; i++) {
      const fragment = new THREE.Mesh(fragmentGeometry, fragmentMaterial)
      fragment.position.copy(crate.position)
      fragment.position.y += Math.random() * 0.3
      fragment.castShadow = true

      // Random rotation
      fragment.rotation.set(
        Math.random() * Math.PI,
        Math.random() * Math.PI,
        Math.random() * Math.PI
      )

      this.scene.add(fragment)

      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 4,
        Math.random() * 2 + 1,
        (Math.random() - 0.5) * 4
      )

      this.animateFlyingPiece(fragment, velocity, 0.96)
    }

    this.createDebrisParticles(crate.position, EnvironmentType.Crate)
  }

  private destroyTree(tree: THREE.Object3D): void {
    // Animate tree falling
    const fallDirection = Math.random() > 0.5 ? 1 : -1
    const fallAxis = Math.random() > 0.5 ? 'x' : 'z'

    const originalRotation = tree.rotation.clone()
    const targetRotation = originalRotation.clone()
    targetRotation[fallAxis] += (Math.PI / 2) * fallDirection

    // Animate the fall
    const duration = 1.5
    let startTime: number | null = null

    const animateFall = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Easing function for realistic falling
      const easeProgress = 1 - Math.pow(1 - progress, 3)

      tree.rotation[fallAxis] = originalRotation[fallAxis] +
        (targetRotation[fallAxis] - originalRotation[fallAxis]) * easeProgress

      if (progress < 1) {
        requestAnimationFrame(animateFall)
      } else {
        // Create impact effect
        this.createTreeFallImpact(tree.position, fallAxis, fallDirection)

        // Remove tree after a delay
        setTimeout(() => {
          this.scene.remove(tree)
        }, 2000)
      }
    }

    requestAnimationFrame(animateFall)

    // Create leaves falling
    this.createLeavesFalling(tree.position)
  }

  private createTreeFallImpact(position: THREE.Vector3, axis: string, direction: number): void {
    // Create impact particles where tree hits ground
    const impactPosition = position.clone()
    if (axis === 'x') {
      impactPosition.x += direction * 3
    } else {
      impactPosition.z += direction * 3
    }

    this.createDebrisParticles(impactPosition, EnvironmentType.Tree)

    // Create dust cloud
    const dustParticles = new ParticleSystem({
      type: ParticleType.Smoke,
      count: 30,
      lifespan: 2,
      speed: 1,
      size: 0.5,
      colors: [0x8B7355, 0xA0826D, 0xBC9A6A],
      gravity: -1,
      spread: 2
    }, impactPosition)
    dustParticles.start()
    this.scene.add(dustParticles.emitter)

    setTimeout(() => {
      this.scene.remove(dustParticles.emitter)
      dustParticles.dispose()
    }, 3000)
  }

  private createLeavesFalling(position: THREE.Vector3): void {
    const leavesParticles = new ParticleSystem({
      type: ParticleType.Earth,
      count: 40,
      lifespan: 4,
      speed: 0.5,
      size: 0.15,
      colors: [0x228b22, 0x2e7d32, 0x1b5e20, 0x4caf50],
      gravity: -2,
      spread: 3
    }, position.clone().add(new THREE.Vector3(0, 3, 0)))
    leavesParticles.start()
    this.scene.add(leavesParticles.emitter)

    setTimeout(() => {
      this.scene.remove(leavesParticles.emitter)
      leavesParticles.dispose()
    }, 5000)
  }

  private destroyPillar(pillar: THREE.Object3D): void {
    // Create crumbling effect
    const pieceGeometry = new THREE.BoxGeometry(0.3, 0.5, 0.3)
    const pieceMaterial = new THREE.MeshStandardMaterial({ color: 0xa0a0a0 })

    for (let i = 0; i < 15; i++) {
      const piece = new THREE.Mesh(pieceGeometry, pieceMaterial)
      piece.position.copy(pillar.position)
      piece.position.y = Math.random() * 8
      piece.castShadow = true

      this.scene.add(piece)

      const velocity = new THREE.Vector3(
        (Math.random() - 0.5) * 3,
        Math.random() * 2,
        (Math.random() - 0.5) * 3
      )

      this.animateFlyingPiece(piece, velocity, 0.98)
    }

    // Create dust cloud
    this.createDustCloud(pillar.position)
    this.createDebrisParticles(pillar.position, EnvironmentType.Pillar)
  }

  private destroyGenericObject(object: THREE.Object3D): void {
    // Generic destruction with particles
    this.createDebrisParticles(object.position, EnvironmentType.Rock)
  }

  private animateFlyingPiece(piece: THREE.Mesh, velocity: THREE.Vector3, damping: number): void {
    const gravity = -9.8
    let startTime: number | null = null

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime
      const elapsed = (currentTime - startTime) / 1000 // Convert to seconds

      if (elapsed < 3) { // Animate for 3 seconds
        // Update position
        piece.position.x += velocity.x * 0.016 // ~60fps timestep
        piece.position.y += velocity.y * 0.016
        piece.position.z += velocity.z * 0.016

        // Apply gravity
        velocity.y += gravity * 0.016

        // Apply damping
        velocity.x *= damping
        velocity.z *= damping

        // Rotate piece
        piece.rotation.x += 0.05
        piece.rotation.y += 0.03
        piece.rotation.z += 0.04

        // Remove if fallen below ground
        if (piece.position.y < -1) {
          this.scene.remove(piece)
        } else {
          requestAnimationFrame(animate)
        }
      } else {
        this.scene.remove(piece)
      }
    }

    requestAnimationFrame(animate)
  }

  private createDustCloud(position: THREE.Vector3): void {
    const dustParticles = new ParticleSystem({
      type: ParticleType.Smoke,
      count: 50,
      lifespan: 3,
      speed: 2,
      size: 0.8,
      colors: [0x8B7355, 0xA0826D, 0xBC9A6A],
      gravity: -0.5,
      spread: 3
    }, position.clone().add(new THREE.Vector3(0, 0.5, 0)))
    dustParticles.start()
    this.scene.add(dustParticles.emitter)

    setTimeout(() => {
      this.scene.remove(dustParticles.emitter)
      dustParticles.dispose()
    }, 4000)
  }

  public setWeather(weather: WeatherConfig): void {
    // Remove existing weather particles
    if (this.weatherParticles) {
      this.scene.remove(this.weatherParticles.emitter)
      this.weatherParticles.dispose()
      this.weatherParticles = undefined
    }

    if (weather.type === WeatherType.Clear) {
      return
    }

    // Create weather particles based on type
    const weatherConfig = this.getWeatherParticleConfig(weather)
    if (weatherConfig) {
      this.weatherParticles = new ParticleSystem(weatherConfig, new THREE.Vector3(0, 20, 0))
      this.weatherParticles.start()
      this.scene.add(this.weatherParticles.emitter)
    }

    // Adjust scene properties based on weather
    this.adjustSceneForWeather(weather)
  }

  private getWeatherParticleConfig(weather: WeatherConfig): any {
    const baseConfig = {
      lifespan: 5,
      gravity: -9.8,
      spread: 50
    }

    switch (weather.type) {
      case WeatherType.Rain:
        return {
          ...baseConfig,
          type: ParticleType.Wind,
          count: 100 * weather.intensity,
          lifespan: 3,
          speed: 15,
          size: 0.05,
          color: 0x4FC3F7,
          gravity: -20,
          spread: 40
        }

      case WeatherType.Snow:
        return {
          ...baseConfig,
          type: ParticleType.Ice,
          count: 80 * weather.intensity,
          lifespan: 8,
          speed: 1,
          size: 0.1,
          colors: [0xffffff, 0xf0f8ff, 0xe6e6fa],
          gravity: -0.5,
          spread: 45
        }

      case WeatherType.Storm:
        return {
          ...baseConfig,
          type: ParticleType.Lightning,
          count: 150 * weather.intensity,
          lifespan: 2,
          speed: 25,
          size: 0.08,
          colors: [0x4FC3F7, 0x81D4FA, 0xB3E5FC],
          gravity: -30,
          spread: 35
        }

      case WeatherType.Fog:
        return {
          ...baseConfig,
          type: ParticleType.Smoke,
          count: 30 * weather.intensity,
          lifespan: 10,
          speed: 0.5,
          size: 2,
          color: 0xd3d3d3,
          gravity: 0,
          spread: 60
        }

      default:
        return null
    }
  }

  private adjustSceneForWeather(weather: WeatherConfig): void {
    if (!this.ambientLight || !this.directionalLight) return

    switch (weather.type) {
      case WeatherType.Rain:
      case WeatherType.Storm:
        // Darker, more blue-ish lighting
        this.ambientLight.color.setHex(0x404050)
        this.ambientLight.intensity = 0.3
        this.directionalLight.color.setHex(0x606080)
        this.directionalLight.intensity = 0.4

        // Add thicker fog
        if (this.fog) {
          this.fog.near = 5
          this.fog.far = 30
        }
        break

      case WeatherType.Fog:
        // Very diffused lighting
        this.ambientLight.color.setHex(0x808080)
        this.ambientLight.intensity = 0.5
        this.directionalLight.intensity = 0.2

        // Very thick fog
        if (this.fog) {
          this.fog.near = 2
          this.fog.far = 15
        }
        break

      case WeatherType.Snow:
        // Brighter, diffused lighting
        this.ambientLight.color.setHex(0xf0f0f0)
        this.ambientLight.intensity = 0.6
        this.directionalLight.color.setHex(0xe0e0ff)
        this.directionalLight.intensity = 0.5

        // Light fog
        if (this.fog) {
          this.fog.near = 10
          this.fog.far = 50
        }
        break

      default:
        // Normal lighting
        this.ambientLight.color.setHex(0x404040)
        this.ambientLight.intensity = 0.4
        this.directionalLight.color.setHex(0xffffff)
        this.directionalLight.intensity = 0.8

        // Normal fog
        if (this.fog) {
          this.fog.near = 10
          this.fog.far = 100
        }
    }
  }

  public setDayNightCycle(enabled: boolean, speed: number = 0.1): void {
    this.dayNightCycleSpeed = enabled ? speed : 0
  }

  public setTimeOfDay(hour: number): void {
    this.timeOfDay = Math.max(0, Math.min(24, hour))
    this.updateDayNightLighting()
  }

  private updateDayNightLighting(): void {
    if (!this.ambientLight || !this.directionalLight) return

    const hour = this.timeOfDay
    let skyColor, ambientIntensity, sunIntensity, sunColor

    if (hour >= 6 && hour < 12) {
      // Morning
      const morningProgress = (hour - 6) / 6
      skyColor = new THREE.Color().lerpColors(
        new THREE.Color(0xFF6B35), // Dawn orange
        new THREE.Color(0x87CEEB), // Day blue
        morningProgress
      )
      ambientIntensity = 0.3 + morningProgress * 0.3
      sunIntensity = 0.5 + morningProgress * 0.5
      sunColor = new THREE.Color(0xFFEB3B) // Warm yellow
    } else if (hour >= 12 && hour < 18) {
      // Afternoon
      const afternoonProgress = (hour - 12) / 6
      skyColor = new THREE.Color(0x87CEEB) // Day blue
      ambientIntensity = 0.6 - afternoonProgress * 0.2
      sunIntensity = 1.0 - afternoonProgress * 0.3
      sunColor = new THREE.Color(0xFFFFFF) // White
    } else if (hour >= 18 && hour < 21) {
      // Evening
      const eveningProgress = (hour - 18) / 3
      skyColor = new THREE.Color().lerpColors(
        new THREE.Color(0x87CEEB), // Day blue
        new THREE.Color(0xFF6B35), // Sunset orange
        eveningProgress
      )
      ambientIntensity = 0.4 - eveningProgress * 0.3
      sunIntensity = 0.7 - eveningProgress * 0.5
      sunColor = new THREE.Color().lerpColors(
        new THREE.Color(0xFFFFFF), // White
        new THREE.Color(0xFF6B35), // Orange
        eveningProgress
      )
    } else {
      // Night
      skyColor = new THREE.Color(0x0C1445) // Dark blue
      ambientIntensity = 0.1
      sunIntensity = 0.2
      sunColor = new THREE.Color(0xB0C4DE) // Moonlight blue
    }

    // Apply lighting changes
    this.ambientLight.color.copy(skyColor)
    this.ambientLight.intensity = ambientIntensity
    this.directionalLight.color.copy(sunColor)
    this.directionalLight.intensity = sunIntensity

    // Update sun/moon position
    const sunAngle = ((hour - 6) / 24) * Math.PI * 2 - Math.PI / 2
    this.directionalLight.position.x = Math.cos(sunAngle) * 30
    this.directionalLight.position.y = Math.sin(sunAngle) * 30
    this.directionalLight.position.z = 10

    // Update scene background
    this.scene.background = skyColor

    // Adjust fog based on time
    if (this.fog) {
      if (hour >= 20 || hour < 6) {
        // Night - thicker fog
        this.fog.near = 8
        this.fog.far = 40
      } else {
        // Day - normal fog
        this.fog.near = 10
        this.fog.far = 100
      }
    }
  }

  public update(deltaTime: number): void {
    // Update day/night cycle
    if (this.dayNightCycleSpeed > 0) {
      this.timeOfDay += this.dayNightCycleSpeed * deltaTime
      if (this.timeOfDay >= 24) {
        this.timeOfDay -= 24
      }
      this.updateDayNightLighting()
    }

    // Update weather particles
    if (this.weatherParticles) {
      this.weatherParticles.update(deltaTime)
    }
  }

  public getEnvironmentObject(id: string): EnvironmentObject | undefined {
    return this.environmentObjects.get(id)
  }

  public getAllEnvironmentObjects(): EnvironmentObject[] {
    return Array.from(this.environmentObjects.values())
  }

  public dispose(): void {
    // Remove all environment objects
    this.environmentObjects.forEach((envObject) => {
      if (envObject.mesh) {
        this.scene.remove(envObject.mesh)
      }
    })
    this.environmentObjects.clear()

    // Remove weather particles
    if (this.weatherParticles) {
      this.scene.remove(this.weatherParticles.emitter)
      this.weatherParticles.dispose()
      this.weatherParticles = undefined
    }
  }
}