import * as THREE from 'three'
import { CameraSettings, SceneConfig, EnvironmentObject } from '@/types'

export class CombatScene {
  public scene: THREE.Scene
  public camera: THREE.PerspectiveCamera | THREE.OrthographicCamera
  public renderer: THREE.WebGLRenderer
  public clock: THREE.Clock

  private config: SceneConfig
  private cameraSettings: CameraSettings
  private environmentObjects: Map<string, EnvironmentObject> = new Map()
  private gridHelper?: THREE.GridHelper
  private ambientLight?: THREE.AmbientLight
  private directionalLight?: THREE.DirectionalLight

  constructor(config: SceneConfig, cameraSettings: CameraSettings) {
    this.config = config
    this.cameraSettings = cameraSettings
    this.clock = new THREE.Clock()

    this.initScene()
    this.initCamera()
    this.initRenderer()
    this.initLighting()
    this.initEnvironment()
  }

  private initScene(): void {
    this.scene = new THREE.Scene()
    this.scene.fog = new THREE.Fog(0x000000, 10, 100)

    // Set background based on time of day
    const skyColor = this.calculateSkyColor()
    this.scene.background = new THREE.Color(skyColor)
  }

  private initCamera(): void {
    if (this.cameraSettings.type === 'perspective') {
      this.camera = new THREE.PerspectiveCamera(
        this.cameraSettings.fov,
        window.innerWidth / window.innerHeight,
        this.cameraSettings.near,
        this.cameraSettings.far
      )
    } else {
      const aspect = window.innerWidth / window.innerHeight
      const frustumSize = 50
      this.camera = new THREE.OrthographicCamera(
        frustumSize * aspect / -2,
        frustumSize * aspect / 2,
        frustumSize / 2,
        frustumSize / -2,
        this.cameraSettings.near,
        this.cameraSettings.far
      )
    }

    this.camera.position.copy(this.cameraSettings.position)
    this.camera.lookAt(this.cameraSettings.target)
  }

  private initRenderer(): void {
    this.renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    })

    this.renderer.setSize(window.innerWidth, window.innerHeight)
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    this.renderer.shadowMap.enabled = true
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping
    this.renderer.toneMappingExposure = 1.2

    // Enable gamma correction
    this.renderer.outputColorSpace = THREE.SRGBColorSpace
    this.renderer.gammaFactor = 2.2
  }

  private initLighting(): void {
    // Ambient light
    this.ambientLight = new THREE.AmbientLight(
      this.config.lighting.ambientColor,
      this.config.lighting.ambientIntensity
    )
    this.scene.add(this.ambientLight)

    // Directional light (sun/moon)
    this.directionalLight = new THREE.DirectionalLight(
      this.config.lighting.directionalColor,
      this.config.lighting.directionalIntensity
    )

    this.directionalLight.position.copy(this.config.lighting.directionalPosition)
    this.directionalLight.castShadow = this.config.lighting.shadows

    if (this.config.lighting.shadows) {
      this.directionalLight.shadow.mapSize.width = 2048
      this.directionalLight.shadow.mapSize.height = 2048
      this.directionalLight.shadow.camera.near = 0.5
      this.directionalLight.shadow.camera.far = 50
      this.directionalLight.shadow.camera.left = -20
      this.directionalLight.shadow.camera.right = 20
      this.directionalLight.shadow.camera.top = 20
      this.directionalLight.shadow.camera.bottom = -20
      this.directionalLight.shadow.bias = -0.0001
    }

    this.scene.add(this.directionalLight)
  }

  private initEnvironment(): void {
    // Create ground
    this.createGround()

    // Create grid overlay
    if (this.config.gridSize > 0) {
      this.createGrid()
    }

    // Add environmental objects
    this.createEnvironmentObjects()
  }

  private createGround(): void {
    const geometry = new THREE.PlaneGeometry(100, 100)
    const material = this.createTerrainMaterial()

    const ground = new THREE.Mesh(geometry, material)
    ground.rotation.x = -Math.PI / 2
    ground.receiveShadow = true
    ground.name = 'ground'

    this.scene.add(ground)
  }

  private createTerrainMaterial(): THREE.Material {
    switch (this.config.terrainType) {
      case 'grass':
        return new THREE.MeshStandardMaterial({
          color: 0x3a5f3a,
          roughness: 0.8,
          metalness: 0.1
        })
      case 'stone':
        return new THREE.MeshStandardMaterial({
          color: 0x666666,
          roughness: 0.9,
          metalness: 0.1
        })
      case 'sand':
        return new THREE.MeshStandardMaterial({
          color: 0xc4a57b,
          roughness: 0.9,
          metalness: 0.0
        })
      case 'snow':
        return new THREE.MeshStandardMaterial({
          color: 0xffffff,
          roughness: 0.4,
          metalness: 0.0
        })
      case 'dungeon':
        return new THREE.MeshStandardMaterial({
          color: 0x2a2a2a,
          roughness: 0.8,
          metalness: 0.2
        })
      default:
        return new THREE.MeshStandardMaterial({
          color: 0x3a5f3a,
          roughness: 0.8,
          metalness: 0.1
        })
    }
  }

  private createGrid(): void {
    const gridColor = 0x444444
    const gridDivisions = this.config.gridSize / this.config.cellSize

    this.gridHelper = new THREE.GridHelper(
      this.config.gridSize,
      gridDivisions,
      gridColor,
      gridColor
    )

    // Make grid semi-transparent
    const gridMaterial = this.gridHelper.material as THREE.LineBasicMaterial
    gridMaterial.opacity = 0.3
    gridMaterial.transparent = true

    this.scene.add(this.gridHelper)
  }

  private createEnvironmentObjects(): void {
    // Add some default environment objects
    this.addTree(10, 0, 10)
    this.addRock(-15, 0, 5)
    this.addPillar(0, 0, -20)
    this.addBarrel(8, 0, -8)
  }

  private calculateSkyColor(): number {
    const hour = this.config.timeOfDay
    if (hour >= 6 && hour < 12) {
      // Morning: bright blue
      return 0x87CEEB
    } else if (hour >= 12 && hour < 18) {
      // Afternoon: slightly darker blue
      return 0x4A90E2
    } else if (hour >= 18 && hour < 21) {
      // Evening: orange/pink
      return 0xFF6B35
    } else {
      // Night: dark blue
      return 0x0C1445
    }
  }

  public addTree(x: number, y: number, z: number): void {
    const group = new THREE.Group()

    // Trunk
    const trunkGeometry = new THREE.CylinderGeometry(0.5, 0.8, 4)
    const trunkMaterial = new THREE.MeshStandardMaterial({ color: 0x4a3c28 })
    const trunk = new THREE.Mesh(trunkGeometry, trunkMaterial)
    trunk.position.y = 2
    trunk.castShadow = true
    trunk.receiveShadow = true

    // Leaves
    const leavesGeometry = new THREE.ConeGeometry(3, 6)
    const leavesMaterial = new THREE.MeshStandardMaterial({ color: 0x228b22 })
    const leaves = new THREE.Mesh(leavesGeometry, leavesMaterial)
    leaves.position.y = 6
    leaves.castShadow = true

    group.add(trunk)
    group.add(leaves)
    group.position.set(x, y, z)

    const treeObj: EnvironmentObject = {
      id: `tree_${Date.now()}`,
      type: 'tree',
      position: new THREE.Vector3(x, y, z),
      rotation: new THREE.Euler(0, Math.random() * Math.PI * 2, 0),
      scale: new THREE.Vector3(1, 1, 1),
      destructible: true,
      health: 50,
      mesh: group
    }

    this.environmentObjects.set(treeObj.id, treeObj)
    this.scene.add(group)
  }

  public addRock(x: number, y: number, z: number): void {
    const geometry = new THREE.DodecahedronGeometry(1.5, 0)
    const material = new THREE.MeshStandardMaterial({ color: 0x808080 })
    const rock = new THREE.Mesh(geometry, material)

    rock.position.set(x, y + 0.75, z)
    rock.rotation.set(
      Math.random() * Math.PI,
      Math.random() * Math.PI,
      Math.random() * Math.PI
    )
    rock.castShadow = true
    rock.receiveShadow = true

    const rockObj: EnvironmentObject = {
      id: `rock_${Date.now()}`,
      type: 'rock',
      position: new THREE.Vector3(x, y, z),
      rotation: rock.rotation,
      scale: new THREE.Vector3(1, 1, 1),
      destructible: false,
      mesh: rock
    }

    this.environmentObjects.set(rockObj.id, rockObj)
    this.scene.add(rock)
  }

  public addPillar(x: number, y: number, z: number): void {
    const geometry = new THREE.CylinderGeometry(1, 1, 8)
    const material = new THREE.MeshStandardMaterial({ color: 0xa0a0a0 })
    const pillar = new THREE.Mesh(geometry, material)

    pillar.position.set(x, y + 4, z)
    pillar.castShadow = true
    pillar.receiveShadow = true

    const pillarObj: EnvironmentObject = {
      id: `pillar_${Date.now()}`,
      type: 'pillar',
      position: new THREE.Vector3(x, y, z),
      rotation: new THREE.Euler(0, 0, 0),
      scale: new THREE.Vector3(1, 1, 1),
      destructible: true,
      health: 100,
      mesh: pillar
    }

    this.environmentObjects.set(pillarObj.id, pillarObj)
    this.scene.add(pillar)
  }

  public addBarrel(x: number, y: number, z: number): void {
    const group = new THREE.Group()

    // Barrel body
    const bodyGeometry = new THREE.CylinderGeometry(1, 1, 2)
    const bodyMaterial = new THREE.MeshStandardMaterial({ color: 0x8B4513 })
    const body = new THREE.Mesh(bodyGeometry, bodyMaterial)
    body.castShadow = true
    body.receiveShadow = true

    // Metal bands
    const bandGeometry = new THREE.TorusGeometry(1.05, 0.1, 8, 16)
    const bandMaterial = new THREE.MeshStandardMaterial({
      color: 0x404040,
      metalness: 0.8,
      roughness: 0.2
    })

    const band1 = new THREE.Mesh(bandGeometry, bandMaterial)
    band1.position.y = 0.8

    const band2 = new THREE.Mesh(bandGeometry, bandMaterial)
    band2.position.y = -0.8

    group.add(body)
    group.add(band1)
    group.add(band2)
    group.position.set(x, y + 1, z)

    const barrelObj: EnvironmentObject = {
      id: `barrel_${Date.now()}`,
      type: 'barrel',
      position: new THREE.Vector3(x, y, z),
      rotation: new THREE.Euler(0, Math.random() * Math.PI * 2, 0),
      scale: new THREE.Vector3(1, 1, 1),
      destructible: true,
      health: 25,
      mesh: group
    }

    this.environmentObjects.set(barrelObj.id, barrelObj)
    this.scene.add(group)
  }

  public updateEnvironment(deltaTime: number): void {
    // Update time-based lighting
    this.updateLighting()

    // Update weather effects if any
    if (this.config.weather) {
      this.updateWeather(deltaTime)
    }
  }

  private updateLighting(): void {
    if (this.directionalLight && this.ambientLight) {
      const skyColor = this.calculateSkyColor()
      const skyColorObj = new THREE.Color(skyColor)

      // Update ambient light color based on time of day
      this.ambientLight.color.copy(skyColorObj)
      this.ambientLight.intensity = this.config.lighting.ambientIntensity *
        (this.config.timeOfDay >= 6 && this.config.timeOfDay <= 18 ? 1 : 0.3)

      // Update directional light position (sun/moon arc)
      const hourAngle = (this.config.timeOfDay - 6) * (Math.PI / 12)
      this.directionalLight.position.x = Math.cos(hourAngle) * 30
      this.directionalLight.position.y = Math.sin(hourAngle) * 30
      this.directionalLight.position.z = 10
    }
  }

  private updateWeather(deltaTime: number): void {
    // Weather effects will be handled by particle system
  }

  public resize(width: number, height: number): void {
    if (this.camera instanceof THREE.PerspectiveCamera) {
      this.camera.aspect = width / height
    } else {
      const aspect = width / height
      const frustumSize = 50
      this.camera.left = frustumSize * aspect / -2
      this.camera.right = frustumSize * aspect / 2
      this.camera.top = frustumSize / 2
      this.camera.bottom = frustumSize / -2
    }

    this.camera.updateProjectionMatrix()
    this.renderer.setSize(width, height)
  }

  public render(): void {
    this.renderer.render(this.scene, this.camera)
  }

  public dispose(): void {
    this.scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.geometry.dispose()
        if (object.material instanceof THREE.Material) {
          object.material.dispose()
        }
      }
    })

    this.renderer.dispose()
  }
}