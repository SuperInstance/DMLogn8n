import * as THREE from 'three'
import { Character, CharacterClass, AnimationState, AnimationClip } from '@/types'
import { gsap } from 'gsap'

export class CharacterAnimator {
  private character: Character
  private mesh: THREE.Object3D
  private animationMixer: THREE.AnimationMixer
  private currentAnimation?: THREE.AnimationAction
  private animationLibrary: Map<string, AnimationClip> = new Map()
  private timelines: Map<string, gsap.core.Timeline> = new Map()
  private animationSpeed: number = 1

  constructor(character: Character, mesh: THREE.Object3D) {
    this.character = character
    this.mesh = mesh
    this.animationMixer = new THREE.AnimationMixer(mesh)

    this.initializeAnimationLibrary()
    this.createCharacterMesh()
  }

  private initializeAnimationLibrary(): void {
    // Initialize character-specific animations based on class
    const classAnimations = this.getClassAnimations()

    classAnimations.forEach(clip => {
      const threeClip = this.createThreeAnimationClip(clip)
      this.animationLibrary.set(clip.name, clip)
    })
  }

  private getClassAnimations(): AnimationClip[] {
    const baseAnimations: AnimationClip[] = [
      {
        name: AnimationState.Idle,
        duration: 2,
        loop: true,
        keyframes: [
          { time: 0, rotation: new THREE.Euler(0, 0, 0) },
          { time: 0.5, rotation: new THREE.Euler(0.02, 0, 0) },
          { time: 1, rotation: new THREE.Euler(-0.02, 0, 0) },
          { time: 1.5, rotation: new THREE.Euler(0.01, 0, 0) },
          { time: 2, rotation: new THREE.Euler(0, 0, 0) }
        ]
      },
      {
        name: AnimationState.Walking,
        duration: 1,
        loop: true,
        keyframes: [
          { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0.1, 0, 0) },
          { time: 0.25, position: new THREE.Vector3(0, 0.1, 0), rotation: new THREE.Euler(0, 0, 0.05) },
          { time: 0.5, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(-0.1, 0, 0) },
          { time: 0.75, position: new THREE.Vector3(0, -0.1, 0), rotation: new THREE.Euler(0, 0, -0.05) },
          { time: 1, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0.1, 0, 0) }
        ]
      },
      {
        name: AnimationState.Running,
        duration: 0.6,
        loop: true,
        keyframes: [
          { time: 0, position: new THREE.Vector3(0, 0.2, 0), rotation: new THREE.Euler(0.2, 0, 0.1) },
          { time: 0.3, position: new THREE.Vector3(0, -0.2, 0), rotation: new THREE.Euler(-0.2, 0, -0.1) },
          { time: 0.6, position: new THREE.Vector3(0, 0.2, 0), rotation: new THREE.Euler(0.2, 0, 0.1) }
        ]
      },
      {
        name: AnimationState.Hurt,
        duration: 0.5,
        loop: false,
        keyframes: [
          { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
          { time: 0.1, position: new THREE.Vector3(-0.5, 0, 0), rotation: new THREE.Euler(0, -0.3, 0.3) },
          { time: 0.3, position: new THREE.Vector3(0.3, 0, 0), rotation: new THREE.Euler(0, 0.2, -0.2) },
          { time: 0.5, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
        ]
      },
      {
        name: AnimationState.Dying,
        duration: 2,
        loop: false,
        keyframes: [
          { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
          { time: 0.5, position: new THREE.Vector3(-0.2, 0, 0), rotation: new THREE.Euler(0.3, 0, 0.5) },
          { time: 1, position: new THREE.Vector3(-0.5, 0.5, 0), rotation: new THREE.Euler(1.2, 0, 0.8) },
          { time: 2, position: new THREE.Vector3(-0.5, 0, 0), rotation: new THREE.Euler(1.57, 0, 0) }
        ]
      }
    ]

    // Add class-specific animations
    const classSpecificAnimations = this.getClassSpecificAnimations()

    return [...baseAnimations, ...classSpecificAnimations]
  }

  private getClassSpecificAnimations(): AnimationClip[] {
    switch (this.character.class) {
      case CharacterClass.Fighter:
        return [
          {
            name: AnimationState.Attacking,
            duration: 0.8,
            loop: false,
            keyframes: [
              { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
              { time: 0.2, position: new THREE.Vector3(0.5, 0, -0.3), rotation: new THREE.Euler(-0.3, 0.5, 0.2) },
              { time: 0.4, position: new THREE.Vector3(1, 0, -0.5), rotation: new THREE.Euler(-0.5, 0.8, 0.3) },
              { time: 0.6, position: new THREE.Vector3(0.3, 0, -0.2), rotation: new THREE.Euler(-0.2, 0.3, 0.1) },
              { time: 0.8, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
            ]
          }
        ]

      case CharacterClass.Wizard:
        return [
          {
            name: AnimationState.Casting,
            duration: 1.5,
            loop: false,
            keyframes: [
              { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
              { time: 0.3, position: new THREE.Vector3(0, 0.2, 0), rotation: new THREE.Euler(0.2, 0, 0.3) },
              { time: 0.8, position: new THREE.Vector3(0, 0.5, 0), rotation: new THREE.Euler(0.5, 0, 0.8) },
              { time: 1.2, position: new THREE.Vector3(0, 0.3, 0), rotation: new THREE.Euler(0.3, 0, 0.5) },
              { time: 1.5, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
            ]
          }
        ]

      case CharacterClass.Rogue:
        return [
          {
            name: AnimationState.Attacking,
            duration: 0.6,
            loop: false,
            keyframes: [
              { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
              { time: 0.1, position: new THREE.Vector3(-0.5, 0, 0.5), rotation: new THREE.Euler(0, -0.5, 0) },
              { time: 0.3, position: new THREE.Vector3(1.2, 0, -0.3), rotation: new THREE.Euler(0, 0.8, 0) },
              { time: 0.5, position: new THREE.Vector3(0.2, 0, 0.1), rotation: new THREE.Euler(0, 0.2, 0) },
              { time: 0.6, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
            ]
          }
        ]

      case CharacterClass.Cleric:
        return [
          {
            name: AnimationState.Casting,
            duration: 1.2,
            loop: false,
            keyframes: [
              { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
              { time: 0.4, position: new THREE.Vector3(0, 0.3, 0), rotation: new THREE.Euler(0.3, 0, 0.4) },
              { time: 0.8, position: new THREE.Vector3(0, 0.6, 0), rotation: new THREE.Euler(0.6, 0, 0.8) },
              { time: 1.2, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
            ]
          }
        ]

      case CharacterClass.Barbarian:
        return [
          {
            name: AnimationState.Attacking,
            duration: 1,
            loop: false,
            keyframes: [
              { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
              { time: 0.3, position: new THREE.Vector3(-0.8, 0.2, -0.5), rotation: new THREE.Euler(0.5, -0.8, 0.3) },
              { time: 0.6, position: new THREE.Vector3(1.5, 0.5, -0.8), rotation: new THREE.Euler(0.8, 1, 0.6) },
              { time: 0.9, position: new THREE.Vector3(0.3, 0.1, -0.2), rotation: new THREE.Euler(0.2, 0.3, 0.1) },
              { time: 1, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
            ]
          }
        ]

      case CharacterClass.Ranger:
        return [
          {
            name: AnimationState.Attacking,
            duration: 0.9,
            loop: false,
            keyframes: [
              { time: 0, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) },
              { time: 0.2, position: new THREE.Vector3(0, 0.2, -0.3), rotation: new THREE.Euler(-0.3, 0, 0.4) },
              { time: 0.5, position: new THREE.Vector3(0, 0.5, -0.6), rotation: new THREE.Euler(-0.6, 0, 0.8) },
              { time: 0.8, position: new THREE.Vector3(0, 0.2, -0.2), rotation: new THREE.Euler(-0.2, 0, 0.3) },
              { time: 0.9, position: new THREE.Vector3(0, 0, 0), rotation: new THREE.Euler(0, 0, 0) }
            ]
          }
        ]

      default:
        return []
    }
  }

  private createThreeAnimationClip(clip: AnimationClip): THREE.AnimationClip {
    const tracks: THREE.KeyframeTrack[] = []

    // Create position track if keyframes have position
    const positions = clip.keyframes.filter(kf => kf.position).map(kf => kf.position!)
    if (positions.length > 0) {
      const times = clip.keyframes.filter(kf => kf.position).map(kf => kf.time)
      const values = positions.flat()

      tracks.push(
        new THREE.VectorKeyframeTrack(
          `${this.mesh.name}.position`,
          times,
          values
        )
      )
    }

    // Create rotation track if keyframes have rotation
    const rotations = clip.keyframes.filter(kf => kf.rotation).map(kf => kf.rotation!)
    if (rotations.length > 0) {
      const times = clip.keyframes.filter(kf => kf.rotation).map(kf => kf.time)
      const values = rotations.map(r => [r.x, r.y, r.z]).flat()

      tracks.push(
        new THREE.VectorKeyframeTrack(
          `${this.mesh.name}.rotation`,
          times,
          values
        )
      )
    }

    return new THREE.AnimationClip(clip.name, clip.duration, tracks)
  }

  private createCharacterMesh(): void {
    // Create a simple character mesh based on class
    const characterGroup = new THREE.Group()

    // Body
    const bodyGeometry = new THREE.BoxGeometry(1.5, 2, 0.8)
    const bodyMaterial = this.getClassMaterial()
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
    body.position.y = 1.5
    body.castShadow = true
    body.receiveShadow = true

    // Head
    const headGeometry = new THREE.SphereGeometry(0.5)
    const headMaterial = new THREE.MeshStandardMaterial({ color: 0xffdbac })
    const head = new THREE.Mesh(headGeometry, headMaterial)
    head.position.y = 3.2
    head.castShadow = true

    // Arms
    const armGeometry = new THREE.CylinderGeometry(0.2, 0.2, 1.5)
    const armMaterial = bodyMaterial

    const leftArm = new THREE.Mesh(armGeometry, armMaterial)
    leftArm.position.set(-1, 2, 0)
    leftArm.castShadow = true

    const rightArm = new THREE.Mesh(armGeometry, armMaterial)
    rightArm.position.set(1, 2, 0)
    rightArm.castShadow = true

    // Legs
    const legGeometry = new THREE.CylinderGeometry(0.3, 0.3, 1.5)
    const legMaterial = new THREE.MeshStandardMaterial({ color: 0x333333 })

    const leftLeg = new THREE.Mesh(legGeometry, legMaterial)
    leftLeg.position.set(-0.5, 0.75, 0)
    leftLeg.castShadow = true

    const rightLeg = new THREE.Mesh(legGeometry, legMaterial)
    rightLeg.position.set(0.5, 0.75, 0)
    rightLeg.castShadow = true

    // Add class-specific elements
    this.addClassSpecificElements(characterGroup)

    characterGroup.add(body, head, leftArm, rightArm, leftLeg, rightArm)
    characterGroup.name = this.character.id

    // Replace the mesh with our character mesh
    this.mesh.clear()
    this.mesh.add(characterGroup)
  }

  private getClassMaterial(): THREE.MeshStandardMaterial {
    switch (this.character.class) {
      case CharacterClass.Fighter:
        return new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.3 })
      case CharacterClass.Wizard:
        return new THREE.MeshStandardMaterial({ color: 0x4a148c, roughness: 0.8 })
      case CharacterClass.Rogue:
        return new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.9 })
      case CharacterClass.Cleric:
        return new THREE.MeshStandardMaterial({ color: 0xfdd835, roughness: 0.7 })
      case CharacterClass.Barbarian:
        return new THREE.MeshStandardMaterial({ color: 0x5d4037, roughness: 0.8 })
      case CharacterClass.Ranger:
        return new THREE.MeshStandardMaterial({ color: 0x2e7d32, roughness: 0.8 })
      default:
        return new THREE.MeshStandardMaterial({ color: 0x666666 })
    }
  }

  private addClassSpecificElements(group: THREE.Group): void {
    switch (this.character.class) {
      case CharacterClass.Fighter:
        // Add helmet
        const helmetGeometry = new THREE.ConeGeometry(0.6, 0.8)
        const helmetMaterial = new THREE.MeshStandardMaterial({
          color: 0x888888,
          metalness: 0.8
        })
        const helmet = new THREE.Mesh(helmetGeometry, helmetMaterial)
        helmet.position.y = 3.7
        group.add(helmet)
        break

      case CharacterClass.Wizard:
        // Add wizard hat
        const hatGeometry = new THREE.ConeGeometry(0.8, 1.5)
        const hatMaterial = new THREE.MeshStandardMaterial({
          color: 0x4a148c,
          roughness: 0.8
        })
        const hat = new THREE.Mesh(hatGeometry, hatMaterial)
        hat.position.y = 4
        group.add(hat)

        // Add staff
        const staffGeometry = new THREE.CylinderGeometry(0.05, 0.05, 4)
        const staffMaterial = new THREE.MeshStandardMaterial({
          color: 0x8d6e63,
          roughness: 0.9
        })
        const staff = new THREE.Mesh(staffGeometry, staffMaterial)
        staff.position.set(1.5, 3, 0)
        staff.rotation.z = -0.3
        group.add(staff)
        break

      case CharacterClass.Rogue:
        // Add daggers
        const daggerGeometry = new THREE.BoxGeometry(0.1, 0.4, 0.02)
        const daggerMaterial = new THREE.MeshStandardMaterial({
          color: 0x757575,
          metalness: 0.9
        })

        const leftDagger = new THREE.Mesh(daggerGeometry, daggerMaterial)
        leftDagger.position.set(-1.5, 2, 0)
        group.add(leftDagger)

        const rightDagger = new THREE.Mesh(daggerGeometry, daggerMaterial)
        rightDagger.position.set(1.5, 2, 0)
        group.add(rightDagger)
        break

      case CharacterClass.Cleric:
        // Add holy symbol
        const symbolGeometry = new THREE.OctahedronGeometry(0.3)
        const symbolMaterial = new THREE.MeshStandardMaterial({
          color: 0xfdd835,
          metalness: 0.6,
          emissive: 0xfdd835,
          emissiveIntensity: 0.2
        })
        const symbol = new THREE.Mesh(symbolGeometry, symbolMaterial)
        symbol.position.set(0, 2.2, 0.5)
        group.add(symbol)
        break

      case CharacterClass.Barbarian:
        // Add axe
        const axeHandleGeometry = new THREE.CylinderGeometry(0.05, 0.05, 2)
        const axeHandleMaterial = new THREE.MeshStandardMaterial({
          color: 0x8d6e63,
          roughness: 0.9
        })
        const axeHandle = new THREE.Mesh(axeHandleGeometry, axeHandleMaterial)
        axeHandle.position.set(1.5, 2.5, 0)
        axeHandle.rotation.z = -0.5
        group.add(axeHandle)

        const axeHeadGeometry = new THREE.BoxGeometry(0.1, 0.6, 0.8)
        const axeHeadMaterial = new THREE.MeshStandardMaterial({
          color: 0x757575,
          metalness: 0.8
        })
        const axeHead = new THREE.Mesh(axeHeadGeometry, axeHeadMaterial)
        axeHead.position.set(1.5, 3, 0)
        group.add(axeHead)
        break

      case CharacterClass.Ranger:
        // Add bow
        const bowGeometry = new THREE.TorusGeometry(1, 0.05, 8, 16, Math.PI)
        const bowMaterial = new THREE.MeshStandardMaterial({
          color: 0x8d6e63,
          roughness: 0.8
        })
        const bow = new THREE.Mesh(bowGeometry, bowMaterial)
        bow.position.set(1.2, 2.5, 0)
        bow.rotation.y = Math.PI / 2
        group.add(bow)
        break
    }
  }

  public playAnimation(animationName: string, speed: number = 1): void {
    const clip = this.animationLibrary.get(animationName)
    if (!clip) return

    // Stop current animation if it exists
    if (this.currentAnimation) {
      this.currentAnimation.stop()
    }

    // Create and play new animation
    const threeClip = this.createThreeAnimationClip(clip)
    const action = this.animationMixer.clipAction(threeClip)

    action.setLoop(clip.loop ? THREE.LoopRepeat : THREE.LoopOnce, Infinity)
    if (!clip.loop) {
      action.clampWhenFinished = true
    }

    action.setEffectiveTimeScale(speed * this.animationSpeed)
    action.play()

    this.currentAnimation = action
    this.character.animationState = animationName as AnimationState
  }

  public playAttackAnimation(targetPosition?: THREE.Vector3): Promise<void> {
    return new Promise((resolve) => {
      this.playAnimation(AnimationState.Attacking)

      // Add additional movement if target position is provided
      if (targetPosition) {
        const timeline = gsap.timeline()

        // Calculate direction to target
        const direction = new THREE.Vector3()
          .subVectors(targetPosition, this.mesh.position)
          .normalize()

        // Lunge forward
        timeline.to(this.mesh.position, {
          x: this.mesh.position.x + direction.x * 2,
          z: this.mesh.position.z + direction.z * 2,
          duration: 0.4,
          ease: "power2.out"
        })

        // Return to original position
        timeline.to(this.mesh.position, {
          x: this.character.position.x,
          z: this.character.position.z,
          duration: 0.4,
          ease: "power2.in",
          onComplete: () => resolve()
        })
      } else {
        // Animation duration based on clip length
        const clip = this.animationLibrary.get(AnimationState.Attacking)
        setTimeout(resolve, (clip?.duration || 1) * 1000)
      }
    })
  }

  public playCastAnimation(): Promise<void> {
    return new Promise((resolve) => {
      this.playAnimation(AnimationState.Casting)

      const clip = this.animationLibrary.get(AnimationState.Casting)
      setTimeout(resolve, (clip?.duration || 1.5) * 1000)
    })
  }

  public playHurtAnimation(): Promise<void> {
    return new Promise((resolve) => {
      this.playAnimation(AnimationState.Hurt)

      const clip = this.animationLibrary.get(AnimationState.Hurt)
      setTimeout(resolve, (clip?.duration || 0.5) * 1000)
    })
  }

  public playDeathAnimation(): Promise<void> {
    return new Promise((resolve) => {
      this.playAnimation(AnimationState.Dying)

      const clip = this.animationLibrary.get(AnimationState.Dying)
      setTimeout(resolve, (clip?.duration || 2) * 1000)
    })
  }

  public moveToPosition(targetPosition: THREE.Vector3, speed: number = 2): Promise<void> {
    return new Promise((resolve) => {
      const distance = this.mesh.position.distanceTo(targetPosition)
      const duration = distance / speed

      // Determine animation state based on speed
      if (speed > 4) {
        this.playAnimation(AnimationState.Running)
      } else if (speed > 0.5) {
        this.playAnimation(AnimationState.Walking)
      }

      // Move character
      gsap.to(this.mesh.position, {
        x: targetPosition.x,
        y: targetPosition.y,
        z: targetPosition.z,
        duration: duration,
        ease: "power2.inOut",
        onUpdate: () => {
          // Update character position
          this.character.position.copy(this.mesh.position)

          // Rotate to face movement direction
          const direction = new THREE.Vector3()
            .subVectors(targetPosition, this.mesh.position)
            .normalize()

          if (direction.length() > 0.01) {
            const angle = Math.atan2(direction.x, direction.z)
            this.mesh.rotation.y = angle
          }
        },
        onComplete: () => {
          // Return to idle animation
          this.playAnimation(AnimationState.Idle)
          resolve()
        }
      })
    })
  }

  public update(deltaTime: number): void {
    this.animationMixer.update(deltaTime)
  }

  public setAnimationSpeed(speed: number): void {
    this.animationSpeed = speed
  }

  public getCurrentAnimation(): string {
    return this.character.animationState
  }

  public dispose(): void {
    this.animationMixer.uncacheRoot(this.mesh)

    // Clear timelines
    this.timelines.forEach(timeline => timeline.kill())
    this.timelines.clear()
  }
}