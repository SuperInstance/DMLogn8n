/**
 * Spell Casting System for VR D&D
 * Handles spell effects, gestures, and visual/audio feedback
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export class SpellCastingSystem {
  constructor(arvrCore, options = {}) {
    this.arvrCore = arvrCore;
    this.options = {
      gestureRecognition: options.gestureRecognition || null,
      audio: options.audio || null,
      physics: options.physics || null,
      enableParticles: options.enableParticles !== false,
      enablePhysics: options.enablePhysics !== false,
      enableSpatialAudio: options.enableSpatialAudio !== false,
      maxActiveSpells: options.maxActiveSpells || 20,
      ...options
    };

    this.spells = new Map();
    this.activeSpells = new Map();
    this.spellLibrary = null;
    this.particleSystem = null;
    this.loader = new GLTFLoader();

    // Spell casting state
    this.isCasting = false;
    this.currentSpell = null;
    this.castProgress = 0;
    this.gestureSequence = [];
    this.requiredGestures = [];

    // Visual effects
    this.spellEffects = new Map();
    this.effectPool = [];
  }

  async initialize() {
    await this.loadSpellLibrary();
    await this.initializeParticleSystem();
    this.setupGestureRecognition();
    this.setupAudioSystem();
    this.setupEventHandlers();

    console.log('Spell Casting System initialized');
  }

  async loadSpellLibrary() {
    this.spellLibrary = {
      // Cantrips
      'firebolt': {
        name: 'Firebolt',
        level: 0,
        school: 'evocation',
        castingTime: 'action',
        range: 120,
        damage: '1d10 fire',
        gestures: ['point', 'flick'],
        incantation: 'Ignis',
        effects: ['projectile', 'fire_trail', 'explosion'],
        sound: 'fire_cast',
        model: '/assets/models/spells/firebolt.gltf',
        color: 0xff6b35,
        particleColor: 0xff4500,
        duration: 2000
      },

      'magicmissile': {
        name: 'Magic Missile',
        level: 1,
        school: 'evocation',
        castingTime: 'action',
        range: 120,
        damage: '3d4+3 force',
        gestures: ['circle', 'point', 'release'],
        incantation: 'Sagitta',
        effects: ['missiles', 'tracking', 'impact'],
        sound: 'magic_missile',
        model: '/assets/models/spells/magicmissile.gltf',
        color: 0x9b59b6,
        particleColor: 0x8e44ad,
        duration: 3000
      },

      'fireball': {
        name: 'Fireball',
        level: 3,
        school: 'evocation',
        castingTime: 'action',
        range: 150,
        damage: '8d6 fire',
        gestures: ['circle', 'push', 'release'],
        incantation: 'Ignis Sphaera',
        effects: ['charging', 'projectile', 'large_explosion', 'fire_spread'],
        sound: 'fireball_cast',
        model: '/assets/models/spells/fireball.gltf',
        color: 0xff4757,
        particleColor: 0xff6348,
        duration: 4000,
        radius: 20
      },

      'lightningbolt': {
        name: 'Lightning Bolt',
        level: 3,
        school: 'evocation',
        castingTime: 'action',
        range: 100,
        damage: '8d6 lightning',
        gestures: ['raise', 'sweep', 'point'],
        incantation: 'Fulgur',
        effects: ['charging', 'beam', 'chain_lightning'],
        sound: 'lightning_cast',
        model: '/assets/models/spells/lightning.gltf',
        color: 0x3498db,
        particleColor: 0x2980b9,
        duration: 2000
      },

      'shield': {
        name: 'Shield',
        level: 1,
        school: 'abjuration',
        castingTime: 'reaction',
        range: 'self',
        effects: ['barrier', 'deflection'],
        gestures: ['block', 'spread'],
        incantation: 'Protectum',
        sound: 'shield_cast',
        model: '/assets/models/spells/shield.gltf',
        color: 0x3498db,
        particleColor: 0x85c1e9,
        duration: 60000,
        protective: true
      },

      'mistystep': {
        name: 'Misty Step',
        level: 2,
        school: 'conjuration',
        castingTime: 'bonus',
        range: 30,
        effects: ['teleport_vfx', 'mist'],
        gestures: ['spin', 'step'],
        incantation: 'Transitus',
        sound: 'teleport_cast',
        model: '/assets/models/spells/teleport.gltf',
        color: 0x95afc0,
        particleColor: 0xdfe6e9,
        duration: 1000,
        teleportRange: 30
      },

      'healingword': {
        name: 'Healing Word',
        level: 1,
        school: 'evocation',
        castingTime: 'bonus',
        range: 60,
        healing: '1d4 + Wisdom modifier',
        gestures: ['raise', 'bless'],
        incantation: 'Sanatio',
        effects: ['healing_aura', 'light_particles'],
        sound: 'healing_cast',
        model: '/assets/models/spells/heal.gltf',
        color: 0x2ecc71,
        particleColor: 0x27ae60,
        duration: 2000
      },

      'invisibility': {
        name: 'Invisibility',
        level: 2,
        school: 'illusion',
        castingTime: 'action',
        range: 'touch',
        duration: '1 hour',
        gestures: ['hide', 'vanish'],
        incantation: 'Invisibilis',
        effects: ['transparency', 'distortion'],
        sound: 'illusion_cast',
        model: '/assets/models/spells/invisibility.gltf',
        color: 0xecf0f1,
        particleColor: 0xbdc3c7,
        duration: 3600000
      }
    };
  }

  async initializeParticleSystem() {
    if (!this.options.enableParticles) return;

    // Create particle system container
    this.particleSystem = {
      particles: [],
      maxParticles: 1000,
      particleGeometry: new THREE.BufferGeometry(),
      particleMaterial: new THREE.PointsMaterial({
        size: 0.1,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
      })
    };

    // Initialize particle buffer
    const positions = new Float32Array(this.particleSystem.maxParticles * 3);
    const colors = new Float32Array(this.particleSystem.maxParticles * 3);
    const sizes = new Float32Array(this.particleSystem.maxParticles);

    this.particleSystem.particleGeometry.setAttribute(
      'position',
      new THREE.BufferAttribute(positions, 3)
    );
    this.particleSystem.particleGeometry.setAttribute(
      'color',
      new THREE.BufferAttribute(colors, 3)
    );
    this.particleSystem.particleGeometry.setAttribute(
      'size',
      new THREE.BufferAttribute(sizes, 1)
    );

    const particleSystem = new THREE.Points(
      this.particleSystem.particleGeometry,
      this.particleSystem.particleMaterial
    );

    this.arvrCore.scene.add(particleSystem);
    this.particleSystem.points = particleSystem;
  }

  setupGestureRecognition() {
    if (!this.options.gestureRecognition) return;

    this.options.gestureRecognition.on('gestureDetected', (gesture) => {
      this.handleGestureDetected(gesture);
    });

    this.options.gestureRecognition.on('gestureSequence', (sequence) => {
      this.handleGestureSequence(sequence);
    });
  }

  setupAudioSystem() {
    if (!this.options.audio) return;

    // Preload spell sounds
    Object.values(this.spellLibrary).forEach(spell => {
      if (spell.sound) {
        this.options.audio.loadSound(spell.sound, `/assets/audio/spells/${spell.sound}.mp3`);
      }
    });
  }

  setupEventHandlers() {
    this.arvrCore.on('pinchStart', (data) => {
      if (this.currentSpell) {
        this.startSpellCast();
      }
    });

    this.arvrCore.on('pinchEnd', (data) => {
      if (this.isCasting) {
        this.completeSpellCast();
      }
    });
  }

  async cast(spellId, target, options = {}) {
    const spell = this.spellLibrary[spellId];
    if (!spell) {
      throw new Error(`Spell '${spellId}' not found`);
    }

    if (this.isCasting) {
      throw new Error('Already casting a spell');
    }

    if (this.activeSpells.size >= this.options.maxActiveSpells) {
      throw new Error('Maximum active spells reached');
    }

    this.currentSpell = {
      ...spell,
      id: this.generateSpellId(),
      target: target,
      options: options,
      startTime: Date.now(),
      castProgress: 0,
      gestures: []
    };

    // Start gesture recognition if enabled
    if (this.options.gestureRecognition && spell.gestures) {
      this.requiredGestures = [...spell.gestures];
      this.options.gestureRecognition.startGestureDetection();
    }

    // Play casting sound
    if (this.options.audio && spell.sound) {
      this.options.audio.playSound(spell.sound, {
        spatial: this.options.enableSpatialAudio,
        position: this.arvrCore.camera.position
      });
    }

    this.emit('spellCastStarted', this.currentSpell);
    return this.currentSpell;
  }

  startSpellCast() {
    if (!this.currentSpell) return;

    this.isCasting = true;
    this.castProgress = 0;

    // Show casting progress
    this.showCastingProgress();

    // Start spell effects
    this.createCastingEffects(this.currentSpell);
  }

  completeSpellCast() {
    if (!this.isCasting || !this.currentSpell) return;

    // Validate gestures if required
    if (this.requiredGestures.length > 0) {
      const gesturesMatch = this.validateGestureSequence();
      if (!gesturesMatch) {
        this.emit('spellFailed', { spell: this.currentSpell, reason: 'Incorrect gestures' });
        this.resetSpellCast();
        return;
      }
    }

    // Execute spell effects
    this.executeSpellEffects(this.currentSpell);

    // Add to active spells
    this.activeSpells.set(this.currentSpell.id, this.currentSpell);

    this.emit('spellCastCompleted', this.currentSpell);
    this.resetSpellCast();
  }

  validateGestureSequence() {
    if (this.currentSpell.gestures.length !== this.requiredGestures.length) {
      return false;
    }

    return this.currentSpell.gestures.every((gesture, index) =>
      gesture === this.requiredGestures[index]
    );
  }

  executeSpellEffects(spell) {
    spell.effects.forEach((effect, index) => {
      setTimeout(() => {
        this.createSpellEffect(spell, effect);
      }, index * 200); // Stagger effects
    });

    // Apply spell mechanics
    this.applySpellMechanics(spell);
  }

  createSpellEffect(spell, effectType) {
    const effect = {
      type: effectType,
      spell: spell,
      startTime: Date.now(),
      duration: spell.duration,
      position: spell.target ? spell.target.position.clone() : this.arvrCore.camera.position.clone(),
      elements: []
    };

    switch (effectType) {
      case 'projectile':
        this.createProjectileEffect(effect);
        break;
      case 'explosion':
        this.createExplosionEffect(effect);
        break;
      case 'barrier':
        this.createBarrierEffect(effect);
        break;
      case 'beam':
        this.createBeamEffect(effect);
        break;
      case 'teleport_vfx':
        this.createTeleportEffect(effect);
        break;
      case 'healing_aura':
        this.createHealingEffect(effect);
        break;
      case 'fire_trail':
        this.createFireTrailEffect(effect);
        break;
      case 'tracking':
        this.createTrackingEffect(effect);
        break;
    }

    this.spellEffects.set(effect.id || this.generateEffectId(), effect);
    this.emit('spellEffectCreated', effect);
  }

  createProjectileEffect(effect) {
    const geometry = new THREE.SphereGeometry(0.2, 16, 16);
    const material = new THREE.MeshBasicMaterial({
      color: effect.spell.color,
      emissive: effect.spell.color,
      transparent: true,
      opacity: 0.8
    });

    const projectile = new THREE.Mesh(geometry, material);
    projectile.position.copy(this.arvrCore.camera.position);
    projectile.position.y -= 0.5;

    // Add glow effect
    const glowGeometry = new THREE.SphereGeometry(0.3, 16, 16);
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: effect.spell.color,
      transparent: true,
      opacity: 0.3
    });
    const glow = new THREE.Mesh(glowGeometry, glowMaterial);
    projectile.add(glow);

    this.arvrCore.scene.add(projectile);
    effect.elements.push(projectile);
    effect.projectile = projectile;

    // Animate projectile
    this.animateProjectile(effect);
  }

  createExplosionEffect(effect) {
    // Create explosion particles
    const particleCount = 50;
    const particles = [];

    for (let i = 0; i < particleCount; i++) {
      const particle = this.createExplosionParticle(effect);
      particles.push(particle);
      this.arvrCore.scene.add(particle);
    }

    effect.elements.push(...particles);
    effect.particles = particles;

    // Create shockwave
    const shockwaveGeometry = new THREE.RingGeometry(0.1, 2, 32);
    const shockwaveMaterial = new THREE.MeshBasicMaterial({
      color: effect.spell.color,
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    });

    const shockwave = new THREE.Mesh(shockwaveGeometry, shockwaveMaterial);
    shockwave.position.copy(effect.position);
    shockwave.rotation.x = -Math.PI / 2;

    this.arvrCore.scene.add(shockwave);
    effect.elements.push(shockwave);
    effect.shockwave = shockwave;

    // Animate explosion
    this.animateExplosion(effect);
  }

  createBarrierEffect(effect) {
    const geometry = new THREE.PlaneGeometry(3, 3);
    const material = new THREE.MeshBasicMaterial({
      color: effect.spell.color,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    });

    const barrier = new THREE.Mesh(geometry, material);
    barrier.position.copy(effect.position);

    // Add magical runes
    this.addMagicalRunes(barrier, effect.spell.color);

    this.arvrCore.scene.add(barrier);
    effect.elements.push(barrier);
    effect.barrier = barrier;

    // Animate barrier
    this.animateBarrier(effect);
  }

  createBeamEffect(effect) {
    const points = [];
    points.push(this.arvrCore.camera.position.clone());
    points.push(effect.position.clone());

    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({
      color: effect.spell.color,
      linewidth: 5,
      transparent: true,
      opacity: 0.8
    });

    const beam = new THREE.Line(geometry, material);
    this.arvrCore.scene.add(beam);
    effect.elements.push(beam);
    effect.beam = beam;

    // Add electrical particles
    this.createElectricalParticles(effect);

    // Animate beam
    this.animateBeam(effect);
  }

  createTeleportEffect(effect) {
    // Create mist effect at source and destination
    const sourceMist = this.createMistEffect(this.arvrCore.camera.position);
    const destMist = this.createMistEffect(effect.position);

    this.arvrCore.scene.add(sourceMist);
    this.arvrCore.scene.add(destMist);
    effect.elements.push(sourceMist, destMist);

    // Animate teleport
    this.animateTeleport(effect, sourceMist, destMist);
  }

  createHealingEffect(effect) {
    // Create healing particles
    const particleCount = 30;
    const particles = [];

    for (let i = 0; i < particleCount; i++) {
      const particle = this.createHealingParticle(effect);
      particles.push(particle);
      this.arvrCore.scene.add(particle);
    }

    effect.elements.push(...particles);
    effect.particles = particles;

    // Create healing aura
    const auraGeometry = new THREE.SphereGeometry(1.5, 16, 16);
    const auraMaterial = new THREE.MeshBasicMaterial({
      color: effect.spell.color,
      transparent: true,
      opacity: 0.2,
      side: THREE.BackSide
    });

    const aura = new THREE.Mesh(auraGeometry, auraMaterial);
    aura.position.copy(effect.position);
    this.arvrCore.scene.add(aura);
    effect.elements.push(aura);
    effect.aura = aura;

    // Animate healing
    this.animateHealing(effect);
  }

  createExplosionParticle(effect) {
    const geometry = new THREE.SphereGeometry(0.1, 8, 8);
    const material = new THREE.MeshBasicMaterial({
      color: effect.spell.particleColor,
      transparent: true,
      opacity: 1
    });

    const particle = new THREE.Mesh(geometry, material);
    particle.position.copy(effect.position);

    // Random velocity
    const velocity = new THREE.Vector3(
      (Math.random() - 0.5) * 0.2,
      Math.random() * 0.2,
      (Math.random() - 0.5) * 0.2
    );

    particle.userData = {
      velocity: velocity,
      life: 1.0,
      decay: 0.02
    };

    return particle;
  }

  createHealingParticle(effect) {
    const geometry = new THREE.SphereGeometry(0.05, 8, 8);
    const material = new THREE.MeshBasicMaterial({
      color: effect.spell.color,
      transparent: true,
      opacity: 0.8
    });

    const particle = new THREE.Mesh(geometry, material);
    particle.position.copy(effect.position);

    // Spiral upward motion
    const angle = Math.random() * Math.PI * 2;
    const radius = Math.random() * 0.5;

    particle.userData = {
      angle: angle,
      radius: radius,
      height: 0,
      speed: 0.02,
      riseSpeed: 0.01,
      life: 1.0
    };

    return particle;
  }

  createMistEffect(position) {
    const particleCount = 20;
    const group = new THREE.Group();

    for (let i = 0; i < particleCount; i++) {
      const geometry = new THREE.PlaneGeometry(0.5, 0.5);
      const material = new THREE.MeshBasicMaterial({
        color: 0xdfe6e9,
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide
      });

      const mist = new THREE.Mesh(geometry, material);
      mist.position.copy(position);
      mist.position.add(new THREE.Vector3(
        (Math.random() - 0.5) * 2,
        Math.random() * 0.5,
        (Math.random() - 0.5) * 2
      ));

      mist.userData = {
        velocity: new THREE.Vector3(
          (Math.random() - 0.5) * 0.01,
          Math.random() * 0.02,
          (Math.random() - 0.5) * 0.01
        ),
        rotationSpeed: Math.random() * 0.05
      };

      group.add(mist);
    }

    return group;
  }

  createElectricalParticles(effect) {
    const particleCount = 20;
    const particles = [];

    for (let i = 0; i < particleCount; i++) {
      const geometry = new THREE.SphereGeometry(0.02, 4, 4);
      const material = new THREE.MeshBasicMaterial({
        color: 0xffffff,
        emissive: 0x3498db,
        transparent: true,
        opacity: 0.8
      });

      const particle = new THREE.Mesh(geometry, material);
      particles.push(particle);
      this.arvrCore.scene.add(particle);
    }

    effect.elements.push(...particles);
    effect.electricalParticles = particles;
  }

  animateProjectile(effect) {
    const targetPos = effect.position.clone();
    const startPos = effect.projectile.position.clone();
    const distance = startPos.distanceTo(targetPos);
    const speed = 0.3; // units per frame

    const animate = () => {
      if (!effect.projectile.parent) return;

      const currentPos = effect.projectile.position;
      const direction = targetPos.clone().sub(currentPos).normalize();
      const movement = direction.multiplyScalar(speed);

      currentPos.add(movement);

      // Rotate projectile
      effect.projectile.rotation.x += 0.1;
      effect.projectile.rotation.y += 0.1;

      // Check if reached target
      if (currentPos.distanceTo(targetPos) < 0.2) {
        this.createExplosionEffect(effect);
        this.cleanupEffect(effect);
        return;
      }

      requestAnimationFrame(animate);
    };

    animate();
  }

  animateExplosion(effect) {
    const animate = () => {
      let allDead = true;

      // Animate particles
      effect.particles.forEach(particle => {
        if (!particle.parent) return;

        const userData = particle.userData;
        particle.position.add(userData.velocity);
        particle.userData.life -= userData.decay;

        // Apply gravity
        userData.velocity.y -= 0.001;

        // Fade out
        if (particle.material) {
          particle.material.opacity = userData.life;
        }

        if (userData.life > 0) {
          allDead = false;
        } else {
          this.arvrCore.scene.remove(particle);
        }
      });

      // Animate shockwave
      if (effect.shockwave && effect.shockwave.parent) {
        effect.shockwave.scale.multiplyScalar(1.05);
        effect.shockwave.material.opacity *= 0.95;

        if (effect.shockwave.material.opacity < 0.01) {
          this.arvrCore.scene.remove(effect.shockwave);
        } else {
          allDead = false;
        }
      }

      if (!allDead) {
        requestAnimationFrame(animate);
      } else {
        this.cleanupEffect(effect);
      }
    };

    animate();
  }

  animateBarrier(effect) {
    const animate = () => {
      if (!effect.barrier.parent) return;

      // Pulsing effect
      const pulse = Math.sin(Date.now() * 0.003) * 0.1 + 0.9;
      effect.barrier.material.opacity = 0.3 * pulse;

      // Magical rune rotation
      if (effect.barrier.children.length > 0) {
        effect.barrier.children.forEach(child => {
          child.rotation.z += 0.01;
        });
      }

      // Check duration
      const elapsed = Date.now() - effect.startTime;
      if (elapsed > effect.duration) {
        this.cleanupEffect(effect);
        return;
      }

      requestAnimationFrame(animate);
    };

    animate();
  }

  animateBeam(effect) {
    const animate = () => {
      if (!effect.beam.parent) return;

      // Flickering effect
      const flicker = Math.random() * 0.2 + 0.8;
      effect.beam.material.opacity = 0.8 * flicker;

      // Animate electrical particles
      if (effect.electricalParticles) {
        effect.electricalParticles.forEach((particle, index) => {
          const t = (Date.now() * 0.001 + index * 0.1) % 1;
          const position = new THREE.Vector3().lerpVectors(
            this.arvrCore.camera.position,
            effect.position,
            t
          );
          particle.position.copy(position);

          // Random offset
          particle.position.add(new THREE.Vector3(
            (Math.random() - 0.5) * 0.2,
            (Math.random() - 0.5) * 0.2,
            (Math.random() - 0.5) * 0.2
          ));
        });
      }

      // Check duration
      const elapsed = Date.now() - effect.startTime;
      if (elapsed > 500) { // Beam lasts 500ms
        this.cleanupEffect(effect);
        return;
      }

      requestAnimationFrame(animate);
    };

    animate();
  }

  animateTeleport(effect, sourceMist, destMist) {
    // Animate source mist expanding and fading
    let sourceScale = 0.1;
    let sourceOpacity = 0.8;

    const animateSource = () => {
      sourceScale += 0.02;
      sourceOpacity -= 0.02;

      sourceMist.scale.setScalar(sourceScale);
      sourceMist.children.forEach(child => {
        if (child.material) {
          child.material.opacity = sourceOpacity;
        }
      });

      if (sourceOpacity > 0) {
        requestAnimationFrame(animateSource);
      } else {
        this.arvrCore.scene.remove(sourceMist);
      }
    };

    // Animate destination mist
    let destScale = 2;
    let destOpacity = 0.8;

    const animateDest = () => {
      destScale -= 0.02;
      destOpacity -= 0.01;

      destMist.scale.setScalar(destScale);
      destMist.children.forEach(child => {
        if (child.material) {
          child.material.opacity = destOpacity;
        }
      });

      if (destOpacity > 0) {
        requestAnimationFrame(animateDest);
      } else {
        this.cleanupEffect(effect);
      }
    };

    animateSource();
    setTimeout(animateDest, 500);
  }

  animateHealing(effect) {
    const animate = () => {
      let allDead = true;

      // Animate healing particles
      effect.particles.forEach(particle => {
        if (!particle.parent) return;

        const userData = particle.userData;

        // Spiral motion
        userData.angle += userData.speed;
        userData.height += userData.riseSpeed;

        particle.position.x = effect.position.x + Math.cos(userData.angle) * userData.radius;
        particle.position.y = effect.position.y + userData.height;
        particle.position.z = effect.position.z + Math.sin(userData.angle) * userData.radius;

        particle.userData.life -= 0.01;

        // Fade out
        if (particle.material) {
          particle.material.opacity = userData.life;
        }

        if (userData.life > 0) {
          allDead = false;
        } else {
          this.arvrCore.scene.remove(particle);
        }
      });

      // Animate aura
      if (effect.aura && effect.aura.parent) {
        const pulse = Math.sin(Date.now() * 0.002) * 0.1 + 0.9;
        effect.aura.scale.setScalar(pulse);
        effect.aura.material.opacity = 0.2 * pulse;
      }

      if (!allDead) {
        requestAnimationFrame(animate);
      } else {
        this.cleanupEffect(effect);
      }
    };

    animate();
  }

  addMagicalRunes(barrier, color) {
    const runeCount = 6;
    const radius = 1.2;

    for (let i = 0; i < runeCount; i++) {
      const angle = (i / runeCount) * Math.PI * 2;
      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;

      const geometry = new THREE.PlaneGeometry(0.2, 0.2);
      const material = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.8
      });

      const rune = new THREE.Mesh(geometry, material);
      rune.position.set(x, 0, z);
      rune.lookAt(barrier.position);

      barrier.add(rune);
    }
  }

  applySpellMechanics(spell) {
    // Apply damage, healing, buffs, etc.
    switch (spell.name) {
      case 'Firebolt':
        this.applyDamage(spell, 10); // 1d10 damage
        break;
      case 'Magic Missile':
        this.applyDamage(spell, 13); // 3d4+3 damage
        break;
      case 'Fireball':
        this.applyAreaDamage(spell, 28); // 8d6 damage
        break;
      case 'Healing Word':
        this.applyHealing(spell, 5); // 1d4 healing
        break;
      case 'Shield':
        this.applyBuff(spell, 'AC', 5);
        break;
      case 'Misty Step':
        this.applyTeleport(spell);
        break;
    }
  }

  applyDamage(spell, damage) {
    if (spell.target && spell.target.userData.miniature) {
      const miniature = spell.target.userData.miniature;
      this.emit('spellDamage', { spell, target: miniature, damage });
    }
  }

  applyAreaDamage(spell, damage) {
    // Apply damage to all miniatures in area
    const affectedMiniatures = this.getMiniaturesInArea(spell.position, spell.radius || 5);

    affectedMiniatures.forEach(miniature => {
      this.emit('spellDamage', { spell, target: miniature, damage });
    });
  }

  applyHealing(spell, healing) {
    if (spell.target && spell.target.userData.miniature) {
      const miniature = spell.target.userData.miniature;
      this.emit('spellHealing', { spell, target: miniature, healing });
    }
  }

  applyBuff(spell, buffType, value) {
    if (spell.target && spell.target.userData.miniature) {
      const miniature = spell.target.userData.miniature;
      this.emit('spellBuff', { spell, target: miniature, buffType, value });
    }
  }

  applyTeleport(spell) {
    if (spell.target && spell.target.userData.miniature) {
      const miniature = spell.target.userData.miniature;
      this.emit('spellTeleport', { spell, target: miniature, position: spell.position });
    }
  }

  getMiniaturesInArea(center, radius) {
    // This would need to be implemented based on your miniature manager
    return [];
  }

  handleGestureDetected(gesture) {
    if (this.currentSpell && this.requiredGestures.length > 0) {
      this.currentSpell.gestures.push(gesture.type);

      // Remove from required gestures if matches
      const index = this.requiredGestures.indexOf(gesture.type);
      if (index > -1) {
        this.requiredGestures.splice(index, 1);
      }

      this.emit('gestureDetected', { gesture, spell: this.currentSpell });
    }
  }

  handleGestureSequence(sequence) {
    // Handle complete gesture sequences
    this.emit('gestureSequence', { sequence, spell: this.currentSpell });
  }

  showCastingProgress() {
    // Show UI feedback for casting progress
    const progressElement = document.getElementById('casting-progress');
    if (progressElement) {
      progressElement.style.display = 'block';
      progressElement.style.width = `${this.castProgress}%`;
    }
  }

  createCastingEffects(spell) {
    // Create visual feedback while casting
    const geometry = new THREE.SphereGeometry(0.3, 16, 16);
    const material = new THREE.MeshBasicMaterial({
      color: spell.color,
      transparent: true,
      opacity: 0.5
    });

    const castingOrb = new THREE.Mesh(geometry, material);
    castingOrb.position.copy(this.arvrCore.camera.position);
    castingOrb.position.y -= 0.3;

    this.arvrCore.scene.add(castingOrb);
    this.currentSpell.castingOrb = castingOrb;

    // Animate casting orb
    this.animateCastingOrb(castingOrb);
  }

  animateCastingOrb(orb) {
    const animate = () => {
      if (!orb.parent || !this.isCasting) {
        this.arvrCore.scene.remove(orb);
        return;
      }

      // Pulsing and rotation
      const pulse = Math.sin(Date.now() * 0.005) * 0.1 + 1;
      orb.scale.setScalar(pulse);
      orb.rotation.y += 0.02;

      requestAnimationFrame(animate);
    };

    animate();
  }

  resetSpellCast() {
    this.isCasting = false;
    this.currentSpell = null;
    this.castProgress = 0;
    this.gestureSequence = [];
    this.requiredGestures = [];

    // Hide casting progress
    const progressElement = document.getElementById('casting-progress');
    if (progressElement) {
      progressElement.style.display = 'none';
    }
  }

  cleanupEffect(effect) {
    // Remove all effect elements from scene
    effect.elements.forEach(element => {
      if (element.parent) {
        this.arvrCore.scene.remove(element);
      }
    });

    // Remove from active effects
    const effectId = this.getEffectId(effect);
    if (effectId) {
      this.spellEffects.delete(effectId);
    }

    // Remove from active spells if duration expired
    if (effect.spell) {
      const elapsed = Date.now() - effect.spell.startTime;
      if (elapsed > effect.spell.duration) {
        this.activeSpells.delete(effect.spell.id);
      }
    }
  }

  getEffectId(effect) {
    for (const [id, e] of this.spellEffects.entries()) {
      if (e === effect) return id;
    }
    return null;
  }

  update(deltaTime) {
    // Update all active spell effects
    for (const effect of this.spellEffects.values()) {
      const elapsed = Date.now() - effect.startTime;
      if (elapsed > effect.duration) {
        this.cleanupEffect(effect);
      }
    }

    // Update casting progress
    if (this.isCasting && this.currentSpell) {
      this.castProgress = Math.min(100, this.castProgress + 2);
      this.updateCastingProgress();
    }
  }

  updateCastingProgress() {
    const progressElement = document.getElementById('casting-progress');
    if (progressElement) {
      progressElement.style.width = `${this.castProgress}%`;
    }
  }

  generateSpellId() {
    return 'spell_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  generateEffectId() {
    return 'effect_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  // Event system
  on(event, callback) {
    if (!this.eventListeners) {
      this.eventListeners = new Map();
    }
    if (!this.eventListeners.has(event)) {
      this.eventListeners.set(event, []);
    }
    this.eventListeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.eventListeners && this.eventListeners.has(event)) {
      const listeners = this.eventListeners.get(event);
      const index = listeners.indexOf(callback);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.eventListeners && this.eventListeners.has(event)) {
      this.eventListeners.get(event).forEach(callback => callback(data));
    }
  }

  dispose() {
    // Clear all active spells and effects
    for (const effect of this.spellEffects.values()) {
      this.cleanupEffect(effect);
    }

    this.activeSpells.clear();
    this.spellEffects.clear();

    // Dispose particle system
    if (this.particleSystem && this.particleSystem.points) {
      this.arvrCore.scene.remove(this.particleSystem.points);
    }

    // Reset state
    this.resetSpellCast();
  }
}

export default SpellCastingSystem;