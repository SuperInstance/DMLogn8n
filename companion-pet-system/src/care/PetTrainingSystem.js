/**
 * Advanced pet training system with skill development,
 * behavior modification, and training routines
 */

class PetTrainingSystem {
  constructor() {
    this.trainingSkills = new Map();
    this.trainingMethods = new Map();
    this.trainingPlans = new Map();
    this.trainingProgress = new Map();
    this.trainingEquipment = new Map();
    this.trainingLocations = new Map();
    this.trainers = new Map();

    this.initializeTrainingSkills();
    this.initializeTrainingMethods();
    this.initializeTrainingEquipment();
    this.initializeTrainingLocations();
  }

  initializeTrainingSkills() {
    const skills = {
      // Basic obedience skills
      sit: {
        name: 'Sit',
        category: 'obedience',
        difficulty: 1,
        prerequisites: [],
        effects: { obedience: 10, bonding: 5 },
        trainingTime: 300000, // 5 minutes
        successRate: 0.9,
        ageRequirement: 0
      },
      stay: {
        name: 'Stay',
        category: 'obedience',
        difficulty: 2,
        prerequisites: ['sit'],
        effects: { obedience: 15, patience: 10 },
        trainingTime: 600000, // 10 minutes
        successRate: 0.85,
        ageRequirement: 1
      },
      come: {
        name: 'Come',
        category: 'obedience',
        difficulty: 2,
        prerequisites: ['sit'],
        effects: { obedience: 12, bonding: 8 },
        trainingTime: 450000, // 7.5 minutes
        successRate: 0.8,
        ageRequirement: 1
      },
      heel: {
        name: 'Heel',
        category: 'obedience',
        difficulty: 3,
        prerequisites: ['sit', 'stay'],
        effects: { obedience: 20, coordination: 15 },
        trainingTime: 900000, // 15 minutes
        successRate: 0.75,
        ageRequirement: 2
      },

      // Combat skills
      attack: {
        name: 'Attack Command',
        category: 'combat',
        difficulty: 4,
        prerequisites: ['sit', 'come'],
        effects: { attack: 25, combat_instinct: 20 },
        trainingTime: 1200000, // 20 minutes
        successRate: 0.7,
        ageRequirement: 3
      },
      defend: {
        name: 'Defend',
        category: 'combat',
        difficulty: 4,
        prerequisites: ['stay', 'attack'],
        effects: { defense: 30, protective_instinct: 25 },
        trainingTime: 1200000, // 20 minutes
        successRate: 0.65,
        ageRequirement: 3
      },
      dodge: {
        name: 'Dodge',
        category: 'combat',
        difficulty: 3,
        prerequisites: ['come'],
        effects: { agility: 25, evasion: 20 },
        trainingTime: 900000, // 15 minutes
        successRate: 0.75,
        ageRequirement: 2
      },

      // Agility skills
      jump: {
        name: 'Jump',
        category: 'agility',
        difficulty: 2,
        prerequisites: [],
        effects: { agility: 20, strength: 10 },
        trainingTime: 600000, // 10 minutes
        successRate: 0.85,
        ageRequirement: 1
      },
      climb: {
        name: 'Climb',
        category: 'agility',
        difficulty: 3,
        prerequisites: ['jump'],
        effects: { agility: 25, strength: 20 },
        trainingTime: 900000, // 15 minutes
        successRate: 0.7,
        ageRequirement: 2
      },
      balance: {
        name: 'Balance',
        category: 'agility',
        difficulty: 2,
        prerequisites: [],
        effects: { agility: 15, coordination: 20 },
        trainingTime: 600000, // 10 minutes
        successRate: 0.8,
        ageRequirement: 1
      },

      // Magic skills
      magic_control: {
        name: 'Magic Control',
        category: 'magic',
        difficulty: 4,
        prerequisites: [],
        effects: { magic_affinity: 30, intelligence: 20 },
        trainingTime: 1500000, // 25 minutes
        successRate: 0.6,
        ageRequirement: 3,
        requirements: { magic_potential: true }
      },
      spell_casting: {
        name: 'Spell Casting',
        category: 'magic',
        difficulty: 5,
        prerequisites: ['magic_control'],
        effects: { spell_power: 35, magic_affinity: 25 },
        trainingTime: 1800000, // 30 minutes
        successRate: 0.5,
        ageRequirement: 4,
        requirements: { magic_potential: true }
      },

      // Utility skills
      tracking: {
        name: 'Tracking',
        category: 'utility',
        difficulty: 3,
        prerequisites: ['come'],
        effects: { perception: 25, tracking_skill: 30 },
        trainingTime: 900000, // 15 minutes
        successRate: 0.75,
        ageRequirement: 2
      },
      foraging: {
        name: 'Foraging',
        category: 'utility',
        difficulty: 2,
        prerequisites: [],
        effects: { perception: 15, survival_skill: 20 },
        trainingTime: 600000, // 10 minutes
        successRate: 0.8,
        ageRequirement: 1
      },
      guard: {
        name: 'Guard',
        category: 'utility',
        difficulty: 3,
        prerequisites: ['stay', 'defend'],
        effects: { vigilance: 30, protective_instinct: 25 },
        trainingTime: 900000, // 15 minutes
        successRate: 0.7,
        ageRequirement: 2
      },

      // Social skills
      socialize: {
        name: 'Socialization',
        category: 'social',
        difficulty: 2,
        prerequisites: [],
        effects: { social_skill: 25, confidence: 15 },
        trainingTime: 600000, // 10 minutes
        successRate: 0.85,
        ageRequirement: 0
      },
      teamwork: {
        name: 'Teamwork',
        category: 'social',
        difficulty: 4,
        prerequisites: ['socialize', 'heel'],
        effects: { coordination: 30, social_skill: 25 },
        trainingTime: 1200000, // 20 minutes
        successRate: 0.7,
        ageRequirement: 3
      },

      // Advanced skills
      stealth: {
        name: 'Stealth',
        category: 'advanced',
        difficulty: 4,
        prerequisites: ['stay', 'balance'],
        effects: { stealth_skill: 35, patience: 20 },
        trainingTime: 1200000, // 20 minutes
        successRate: 0.65,
        ageRequirement: 3
      },
      rescue: {
        name: 'Rescue',
        category: 'advanced',
        difficulty: 5,
        prerequisites: ['come', 'defend', 'tracking'],
        effects: { courage: 40, intelligence: 30 },
        trainingTime: 1800000, // 30 minutes
        successRate: 0.5,
        ageRequirement: 4
      }
    };

    for (const [skillId, skillData] of Object.entries(skills)) {
      this.trainingSkills.set(skillId, skillData);
    }
  }

  initializeTrainingMethods() {
    const methods = {
      positive_reinforcement: {
        name: 'Positive Reinforcement',
        description: 'Rewards good behavior with treats and praise',
        effectiveness: 0.9,
        stressLevel: 0.2,
        bondingEffect: 0.8,
        equipment: ['treats', 'clicker'],
        suitableFor: ['all'],
        modifiers: { happiness: 1.2, bonding: 1.3 }
      },
      clicker_training: {
        name: 'Clicker Training',
        description: 'Uses clicker to mark desired behavior',
        effectiveness: 0.85,
        stressLevel: 0.1,
        bondingEffect: 0.7,
        equipment: ['clicker', 'treats'],
        suitableFor: ['young', 'trainable'],
        modifiers: { learning_speed: 1.3, precision: 1.2 }
      },
      target_training: {
        name: 'Target Training',
        description: 'Uses target to guide pet into positions',
        effectiveness: 0.8,
        stressLevel: 0.15,
        bondingEffect: 0.6,
        equipment: ['target_stick', 'treats'],
        suitableFor: ['intelligent', 'curious'],
        modifiers: { coordination: 1.4, focus: 1.2 }
      },
      lure_training: {
        name: 'Lure Training',
        description: 'Uses food or toys to lure pet into position',
        effectiveness: 0.75,
        stressLevel: 0.1,
        bondingEffect: 0.5,
        equipment: ['treats', 'toys'],
        suitableFor: ['food_motivated', 'playful'],
        modifiers: { motivation: 1.5, engagement: 1.3 }
      },
      shaping: {
        name: 'Shaping',
        description: 'Gradually shapes behavior through small steps',
        effectiveness: 0.7,
        stressLevel: 0.3,
        bondingEffect: 0.8,
        equipment: ['treats', 'patience'],
        suitableFor: ['intelligent', 'patient'],
        modifiers: { learning_retention: 1.4, complexity: 1.5 }
      },
      model_training: {
        name: 'Model Training',
        description: 'Pet learns by watching other trained pets',
        effectiveness: 0.8,
        stressLevel: 0.2,
        bondingEffect: 0.4,
        equipment: ['trained_pet', 'treats'],
        suitableFor: ['social', 'observant'],
        modifiers: { social_learning: 1.6, confidence: 1.2 }
      },
      play_training: {
        name: 'Play Training',
        description: 'Incorporates training into play activities',
        effectiveness: 0.85,
        stressLevel: 0.0,
        bondingEffect: 0.9,
        equipment: ['toys', 'treats'],
        suitableFor: ['playful', 'energetic'],
        modifiers: { happiness: 1.5, energy: 1.3 }
      },
      dominance_training: {
        name: 'Dominance Training',
        description: 'Establishes pack hierarchy and leadership',
        effectiveness: 0.6,
        stressLevel: 0.7,
        bondingEffect: 0.3,
        equipment: ['leash', 'confidence'],
        suitableFor: ['dominant_species', 'aggressive'],
        modifiers: { obedience: 1.2, respect: 1.4 }
      }
    };

    for (const [methodId, methodData] of Object.entries(methods)) {
      this.trainingMethods.set(methodId, methodData);
    }
  }

  initializeTrainingEquipment() {
    const equipment = {
      basic: {
        treats: {
          name: 'Training Treats',
          effectiveness: 1.0,
          duration: 0,
          cost: 10,
          description: 'Basic rewards for training'
        },
        clicker: {
          name: 'Training Clicker',
          effectiveness: 1.1,
          duration: 100,
          cost: 25,
          description: 'Clicker for marking desired behavior'
        },
        leash: {
          name: 'Training Leash',
          effectiveness: 1.05,
          duration: 200,
          cost: 30,
          description: 'Leash for control during training'
        }
      },
      intermediate: {
        target_stick: {
          name: 'Target Stick',
          effectiveness: 1.15,
          duration: 150,
          cost: 50,
          description: 'Stick for target training'
        },
        training_whistle: {
          name: 'Training Whistle',
          effectiveness: 1.2,
          duration: 100,
          cost: 60,
          description: 'Whistle for distance commands'
        },
        agility_equipment: {
          name: 'Agility Set',
          effectiveness: 1.3,
          duration: 300,
          cost: 200,
          description: 'Basic agility equipment'
        }
      },
      advanced: {
        magical_treats: {
          name: 'Magical Training Treats',
          effectiveness: 1.4,
          duration: 0,
          cost: 100,
          description: 'Enchanted treats for enhanced learning'
        },
        training_arena: {
          name: 'Training Arena Access',
          effectiveness: 1.5,
          duration: 600,
          cost: 500,
          description: 'Access to specialized training facilities'
        },
        master_trainer: {
          name: 'Master Trainer Session',
          effectiveness: 1.8,
          duration: 120,
          cost: 1000,
          description: 'Session with expert trainer'
        }
      }
    };

    for (const [tier, equipmentList] of Object.entries(equipment)) {
      for (const [itemId, itemData] of Object.entries(equipmentList)) {
        this.trainingEquipment.set(itemId, itemData);
      }
    }
  }

  initializeTrainingLocations() {
    const locations = {
      home: {
        name: 'Home Environment',
        baseEffectiveness: 0.8,
        comfortLevel: 1.0,
        distractions: 0.3,
        suitableFor: ['obedience', 'social'],
        requirements: []
      },
      training_ground: {
        name: 'Training Ground',
        baseEffectiveness: 1.0,
        comfortLevel: 0.8,
        distractions: 0.4,
        suitableFor: ['obedience', 'agility', 'combat'],
        requirements: ['basic_access']
      },
      agility_park: {
        name: 'Agility Park',
        baseEffectiveness: 1.2,
        comfortLevel: 0.9,
        distractions: 0.5,
        suitableFor: ['agility', 'jump', 'balance'],
        requirements: ['park_access']
      },
      magic_academy: {
        name: 'Magic Academy',
        baseEffectiveness: 1.4,
        comfortLevel: 0.7,
        distractions: 0.2,
        suitableFor: ['magic', 'spell_casting'],
        requirements: ['magic_affinity', 'academy_access']
      },
      wilderness: {
        name: 'Wilderness Area',
        baseEffectiveness: 1.1,
        comfortLevel: 0.6,
        distractions: 0.7,
        suitableFor: ['tracking', 'foraging', 'survival'],
        requirements: ['wilderness_access']
      },
      combat_arena: {
        name: 'Combat Arena',
        baseEffectiveness: 1.3,
        comfortLevel: 0.5,
        distractions: 0.3,
        suitableFor: ['combat', 'defense', 'attack'],
        requirements: ['combat_training_access']
      }
    };

    for (const [locationId, locationData] of Object.entries(locations)) {
      this.trainingLocations.set(locationId, locationData);
    }
  }

  // MAIN TRAINING METHODS
  trainPet(pet, skillId, method = 'positive_reinforcement', options = {}) {
    // Validate training session
    const validation = this.validateTrainingSession(pet, skillId, method, options);
    if (!validation.valid) {
      return { success: false, reason: validation.reason, details: validation };
    }

    const skill = this.trainingSkills.get(skillId);
    const trainingMethod = this.trainingMethods.get(method);

    // Calculate training parameters
    const trainingParams = this.calculateTrainingParameters(pet, skill, method, options);

    // Execute training session
    const result = this.executeTrainingSession(pet, skill, method, trainingParams);

    return result;
  }

  validateTrainingSession(pet, skillId, method, options) {
    const skill = this.trainingSkills.get(skillId);
    if (!skill) {
      return { valid: false, reason: 'skill_not_found' };
    }

    const trainingMethod = this.trainingMethods.get(method);
    if (!trainingMethod) {
      return { valid: false, reason: 'method_not_found' };
    }

    // Check pet's ability to train
    if (pet.currentHealth < 50) {
      return { valid: false, reason: 'pet_too_tired' };
    }

    if (pet.energy < 30) {
      return { valid: false, reason: 'insufficient_energy' };
    }

    // Check skill prerequisites
    for (const prereq of skill.prerequisites) {
      if (!pet.unlockedSkills.includes(prereq)) {
        return { valid: false, reason: 'prerequisite_not_met', prerequisite: prereq };
      }
    }

    // Check age requirement
    if (pet.evolutionStage < skill.ageRequirement) {
      return { valid: false, reason: 'insufficient_age', required: skill.ageRequirement };
    }

    // Check special requirements
    if (skill.requirements) {
      for (const [req, value] of Object.entries(skill.requirements)) {
        if (req === 'magic_potential' && !this.hasMagicPotential(pet)) {
          return { valid: false, reason: 'no_magic_potential' };
        }
      }
    }

    // Check method suitability
    if (!this.isMethodSuitable(pet, trainingMethod)) {
      return { valid: false, reason: 'method_not_suitable' };
    }

    return { valid: true };
  }

  calculateTrainingParameters(pet, skill, method, options) {
    const trainingMethod = this.trainingMethods.get(method);
    const location = this.trainingLocations.get(options.location) || this.trainingLocations.get('home');

    // Base success rate
    let successRate = skill.successRate;

    // Method effectiveness
    successRate *= trainingMethod.effectiveness;

    // Location effectiveness
    successRate *= location.baseEffectiveness;

    // Equipment bonuses
    let equipmentBonus = 1.0;
    if (options.equipment) {
      for (const equipmentId of options.equipment) {
        const equipment = this.trainingEquipment.get(equipmentId);
        if (equipment) {
          equipmentBonus *= equipment.effectiveness;
        }
      }
    }
    successRate *= equipmentBonus;

    // Pet factors
    const petModifier = this.calculatePetTrainingModifier(pet, skill);
    successRate *= petModifier;

    // Trainer skill (if applicable)
    const trainerBonus = options.trainer ? this.getTrainerBonus(options.trainer) : 1.0;
    successRate *= trainerBonus;

    // Relationship bonus
    const relationshipBonus = (pet.bonding / 100) * 0.2; // Max 20% bonus
    successRate += relationshipBonus;

    // Clamp success rate
    successRate = Math.max(0.1, Math.min(0.95, successRate));

    return {
      successRate,
      duration: skill.trainingTime,
      energyCost: this.calculateEnergyCost(pet, skill, method),
      stressLevel: trainingMethod.stressLevel,
      experienceGain: skill.difficulty * 10,
      bondingGain: trainingMethod.bondingEffect * 5
    };
  }

  calculatePetTrainingModifier(pet, skill) {
    let modifier = 1.0;

    // Intelligence affects learning
    const intelligenceBonus = (pet.stats.intelligence - 50) / 100;
    modifier += intelligenceBonus;

    // Personality affects training
    const personalityModifier = this.getPersonalityTrainingModifier(pet.personality, skill.category);
    modifier *= personalityModifier;

    // Current mood affects training
    const moodModifier = pet.moodModifier;
    modifier *= moodModifier;

    // Evolution stage affects capacity
    const evolutionBonus = pet.evolutionStage * 0.05;
    modifier += evolutionBonus;

    // Previous training experience
    const trainingExperience = this.getTrainingExperience(pet);
    modifier += trainingExperience * 0.1;

    return Math.max(0.5, modifier);
  }

  getPersonalityTrainingModifier(personality, skillCategory) {
    const modifiers = {
      playful: {
        agility: 1.3,
        social: 1.2,
        combat: 1.1,
        default: 0.9
      },
      serious: {
        obedience: 1.3,
        combat: 1.2,
        magic: 1.1,
        default: 1.0
      },
      curious: {
        magic: 1.4,
        utility: 1.3,
        agility: 1.2,
        default: 1.1
      },
      timid: {
        obedience: 1.2,
        social: 0.8,
        combat: 0.7,
        default: 0.9
      },
      energetic: {
        agility: 1.4,
        combat: 1.3,
        obedience: 1.0,
        default: 1.1
      },
      intelligent: {
        magic: 1.5,
        utility: 1.4,
        advanced: 1.3,
        default: 1.2
      },
      loyal: {
        obedience: 1.4,
        combat: 1.3,
        utility: 1.2,
        default: 1.1
      }
    };

    const personalityModifiers = modifiers[personality.primary] || modifiers.intelligent;
    return personalityModifiers[skillCategory] || personalityModifiers.default;
  }

  isMethodSuitable(pet, method) {
    // Check if method is suitable for pet type/personality
    if (method.suitableFor.includes('all')) return true;

    const petTraits = [
      pet.category,
      pet.personality.primary,
      pet.personality.secondary,
      ...pet.traits
    ];

    for (const suitable of method.suitableFor) {
      if (petTraits.includes(suitable)) {
        return true;
      }
    }

    return false;
  }

  hasMagicPotential(pet) {
    return pet.category === 'magical' ||
           pet.category === 'elemental' ||
           pet.category === 'celestial' ||
           pet.abilities.some(ability => ability.includes('magic')) ||
           pet.traits.includes('magic_affinity');
  }

  calculateEnergyCost(pet, skill, method) {
    const baseCost = skill.difficulty * 5;
    const methodMultiplier = method.effectiveness;
    const intensityMultiplier = options.intensity || 1.0;

    return Math.floor(baseCost * methodMultiplier * intensityMultiplier);
  }

  getTrainerBonus(trainerId) {
    const trainer = this.trainers.get(trainerId);
    return trainer ? trainer.effectiveness : 1.0;
  }

  getTrainingExperience(pet) {
    const progress = this.trainingProgress.get(pet.id);
    return progress ? progress.totalSessions : 0;
  }

  executeTrainingSession(pet, skill, method, params) {
    const sessionId = this.generateTrainingSessionId();
    const startTime = Date.now();

    // Create training session
    const session = {
      id: sessionId,
      petId: pet.id,
      skillId: skill.id,
      method: method,
      params,
      startTime,
      status: 'in_progress',
      progress: 0,
      results: null
    };

    // Consume energy
    pet.energy = Math.max(0, pet.energy - params.energyCost);

    // Apply stress effects
    this.applyStressEffects(pet, params.stressLevel);

    // Simulate training progress
    const success = Math.random() < params.successRate;

    // Calculate results
    const results = {
      success,
      skillLearned: false,
      skillImproved: false,
      experienceGained: params.experienceGain,
      bondingGained: Math.floor(params.bondingGain * (success ? 1.0 : 0.5)),
      energyConsumed: params.energyCost,
      duration: params.duration,
      sideEffects: []
    };

    if (success) {
      // Check if skill is learned
      if (!pet.unlockedSkills.includes(skill.id)) {
        pet.unlockedSkills.push(skill.id);
        results.skillLearned = true;
        results.experienceGained *= 2; // Bonus for new skill
      } else {
        results.skillImproved = true;
      }

      // Apply skill effects
      this.applySkillEffects(pet, skill);

      // Add memory
      pet.addMemory({
        type: 'training_success',
        content: `Successfully trained ${skill.name}`,
        importance: 3
      });
    } else {
      // Training failed
      results.experienceGained = Math.floor(results.experienceGained * 0.3);

      pet.addMemory({
        type: 'training_failure',
        content: `Training ${skill.name} was challenging`,
        importance: 2
      });
    }

    // Apply experience and bonding
    pet.gainExperience(results.experienceGained);
    pet.bonding = Math.min(100, pet.bonding + results.bondingGained);

    // Update training progress
    this.updateTrainingProgress(pet.id, session, results);

    session.status = 'completed';
    session.endTime = Date.now();
    session.results = results;

    return {
      success: true,
      session,
      results
    };
  }

  applyStressEffects(pet, stressLevel) {
    if (stressLevel > 0.5) {
      pet.happiness = Math.max(0, pet.happiness - Math.floor(stressLevel * 10));
    }

    if (stressLevel > 0.7) {
      pet.traits.push('stressed');
      setTimeout(() => {
        const index = pet.traits.indexOf('stressed');
        if (index > -1) pet.traits.splice(index, 1);
      }, 3600000); // Remove stress after 1 hour
    }
  }

  applySkillEffects(pet, skill) {
    for (const [effect, value] of Object.entries(skill.effects)) {
      if (pet.stats[effect] !== undefined) {
        pet.stats[effect] += value;
      } else if (pet.skillEffects) {
        pet.skillEffects[effect] = (pet.skillEffects[effect] || 0) + value;
      }
    }
  }

  updateTrainingProgress(petId, session, results) {
    if (!this.trainingProgress.has(petId)) {
      this.trainingProgress.set(petId, {
        totalSessions: 0,
        successfulSessions: 0,
        skillsLearned: [],
        trainingHistory: [],
        favoriteMethods: new Map(),
        skillProgress: new Map()
      });
    }

    const progress = this.trainingProgress.get(petId);
    progress.totalSessions++;
    if (results.success) progress.successfulSessions++;

    if (results.skillLearned) {
      progress.skillsLearned.push(session.skillId);
    }

    progress.trainingHistory.push({
      sessionId: session.id,
      skillId: session.skillId,
      method: session.method,
      timestamp: session.startTime,
      success: results.success,
      duration: results.duration
    });

    // Update favorite methods
    const methodCount = progress.favoriteMethods.get(session.method) || 0;
    progress.favoriteMethods.set(session.method, methodCount + 1);

    // Update skill progress
    const skillProgress = progress.skillProgress.get(session.skillId) || { attempts: 0, successes: 0 };
    skillProgress.attempts++;
    if (results.success) skillProgress.successes++;
    progress.skillProgress.set(session.skillId, skillProgress);

    // Keep history manageable
    if (progress.trainingHistory.length > 100) {
      progress.trainingHistory.shift();
    }
  }

  // TRAINING PLANS
  createCustomPlan(pet, skills, schedule) {
    const planId = this.generatePlanId();
    const plan = {
      id: planId,
      petId: pet.id,
      skills,
      schedule,
      createdAt: Date.now(),
      status: 'active',
      progress: 0,
      completedSessions: 0,
      totalSessions: 0,
      results: []
    };

    // Calculate total sessions needed
    for (const skillConfig of skills) {
      const skill = this.trainingSkills.get(skillConfig.skillId);
      if (skill) {
        plan.totalSessions += skillConfig.sessions || 1;
      }
    }

    this.trainingPlans.set(planId, plan);

    return { success: true, plan };
  }

  executeTrainingPlan(planId, pet) {
    const plan = this.trainingPlans.get(planId);
    if (!plan) {
      return { success: false, reason: 'plan_not_found' };
    }

    // Find next skill to train
    const nextSkill = this.getNextSkillInPlan(plan);
    if (!nextSkill) {
      return { success: false, reason: 'plan_completed' };
    }

    // Execute training session
    const result = this.trainPet(
      pet,
      nextSkill.skillId,
      nextSkill.method || 'positive_reinforcement',
      nextSkill.options || {}
    );

    if (result.success) {
      plan.completedSessions++;
      plan.progress = (plan.completedSessions / plan.totalSessions) * 100;
      plan.results.push(result.results);

      // Check if plan is complete
      if (plan.completedSessions >= plan.totalSessions) {
        plan.status = 'completed';
        plan.completedAt = Date.now();
      }
    }

    return {
      success: true,
      plan,
      trainingResult: result.results
    };
  }

  getNextSkillInPlan(plan) {
    for (const skillConfig of plan.skills) {
      const sessionsCompleted = plan.results.filter(r =>
        r.skillId === skillConfig.skillId
      ).length;

      if (sessionsCompleted < (skillConfig.sessions || 1)) {
        return skillConfig;
      }
    }

    return null;
  }

  // TRAINING ANALYTICS
  getTrainingReport(petId) {
    const progress = this.trainingProgress.get(petId);
    if (!progress) {
      return { success: false, reason: 'no_training_data' };
    }

    const report = {
      overview: {
        totalSessions: progress.totalSessions,
        successfulSessions: progress.successfulSessions,
        successRate: progress.totalSessions > 0 ? (progress.successfulSessions / progress.totalSessions) * 100 : 0,
        skillsLearned: progress.skillsLearned.length
      },
      favoriteMethods: this.getFavoriteMethods(progress),
      skillMastery: this.calculateSkillMastery(progress),
      trainingTrends: this.calculateTrainingTrends(progress),
      recommendations: this.generateTrainingRecommendations(petId, progress)
    };

    return { success: true, report };
  }

  getFavoriteMethods(progress) {
    const methods = Array.from(progress.favoriteMethods.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3);

    return methods.map(([method, count]) => ({
      method,
      usage: count,
      percentage: (count / progress.totalSessions) * 100
    }));
  }

  calculateSkillMastery(progress) {
    const mastery = {};
    for (const [skillId, skillData] of progress.skillProgress.entries()) {
      const successRate = skillData.attempts > 0 ? (skillData.successes / skillData.attempts) * 100 : 0;
      mastery[skillId] = {
        attempts: skillData.attempts,
        successes: skillData.successes,
        successRate,
        masteryLevel: this.calculateMasteryLevel(successRate, skillData.attempts)
      };
    }
    return mastery;
  }

  calculateMasteryLevel(successRate, attempts) {
    if (attempts < 3) return 'beginning';
    if (successRate >= 90) return 'mastered';
    if (successRate >= 75) return 'advanced';
    if (successRate >= 60) return 'intermediate';
    return 'novice';
  }

  calculateTrainingTrends(progress) {
    const recentHistory = progress.trainingHistory.slice(-10);
    const olderHistory = progress.trainingHistory.slice(-20, -10);

    const recentSuccess = this.calculateSuccessRate(recentHistory);
    const olderSuccess = this.calculateSuccessRate(olderHistory);

    return {
      improving: recentSuccess > olderSuccess,
      recentSuccessRate: recentSuccess,
      trend: recentSuccess > olderSuccess ? 'improving' : 'declining'
    };
  }

  calculateSuccessRate(history) {
    if (history.length === 0) return 0;
    const successes = history.filter(session => session.success).length;
    return (successes / history.length) * 100;
  }

  generateTrainingRecommendations(petId, progress) {
    const recommendations = [];
    const pet = this.getPetById(petId);

    if (!pet) return recommendations;

    // Analyze skill gaps
    const unlearnedSkills = Array.from(this.trainingSkills.keys())
      .filter(skillId => !pet.unlockedSkills.includes(skillId));

    if (unlearnedSkills.length > 0) {
      recommendations.push({
        type: 'new_skills',
        priority: 'medium',
        message: `${unlearnedSkills.length} new skills available to learn`,
        suggestions: unlearnedSkills.slice(0, 3)
      });
    }

    // Analyze training frequency
    const recentSessions = progress.trainingHistory.filter(
      session => Date.now() - session.timestamp < 7 * 24 * 60 * 60 * 1000
    );

    if (recentSessions.length < 3) {
      recommendations.push({
        type: 'frequency',
        priority: 'high',
        message: 'Training frequency is low',
        suggestion: 'Increase training to at least 3 times per week'
      });
    }

    // Analyze success rate
    if (progress.totalSessions > 5 && progress.successfulSessions / progress.totalSessions < 0.7) {
      recommendations.push({
        type: 'success_rate',
        priority: 'high',
        message: 'Training success rate is below 70%',
        suggestion: 'Try different training methods or check pet readiness'
      });
    }

    return recommendations;
  }

  // UTILITY METHODS
  generateTrainingSessionId() {
    return 'training_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
  }

  generatePlanId() {
    return 'plan_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
  }

  getPetById(petId) {
    // This would interface with the pet management system
    return null; // Placeholder
  }

  getAvailableTraining(pet) {
    const availableSkills = [];

    for (const [skillId, skill] of this.trainingSkills.entries()) {
      if (pet.unlockedSkills.includes(skillId)) {
        // Already learned - can practice
        availableSkills.push({
          ...skill,
          status: 'learned',
          canPractice: true
        });
      } else {
        // Check if can learn
        const canLearn = this.validateTrainingSession(pet, skillId, 'positive_reinforcement', {});
        if (canLearn.valid) {
          availableSkills.push({
            ...skill,
            status: 'available',
            canLearn: true
          });
        } else {
          availableSkills.push({
            ...skill,
            status: 'locked',
            reason: canLearn.reason,
            canLearn: false
          });
        }
      }
    }

    return availableSkills;
  }
}

// Additional care system classes (simplified versions)
class PetGroomingSystem {
  getNeeds(pet) {
    return {
      cleanliness: pet.cleanliness,
      needsGrooming: pet.cleanliness < 60,
      urgency: pet.cleanliness < 30 ? 'high' : pet.cleanliness < 60 ? 'medium' : 'low'
    };
  }

  getAvailableServices(pet) {
    return [
      { id: 'basic_brush', name: 'Basic Brushing', effectiveness: 15, cost: 10 },
      { id: 'full_groom', name: 'Full Grooming', effectiveness: 40, cost: 50 },
      { id: 'spa_treatment', name: 'Spa Treatment', effectiveness: 60, cost: 100 }
    ];
  }

  groomPet(pet, method, tools) {
    const effectiveness = method === 'basic' ? 15 : method === 'full' ? 40 : 25;
    pet.cleanliness = Math.min(100, pet.cleanliness + effectiveness);
    pet.happiness = Math.min(100, pet.happiness + 10);

    return {
      success: true,
      cleanlinessGain: effectiveness,
      happinessGain: 10
    };
  }
}

class PetFeedingSystem {
  getRecommendations(pet) {
    return {
      suggestedFoods: [pet.personality.preferences.favoriteFood],
      feedingSchedule: '2-3 times daily',
      portionSize: 'medium'
    };
  }

  getPreferences(pet) {
    return pet.personality.preferences;
  }

  feedPet(pet, food, amount) {
    const hungerGain = typeof amount === 'number' ? amount : 25;
    pet.hunger = Math.min(100, pet.hunger + hungerGain);
    pet.happiness = Math.min(100, pet.happiness + 5);

    return {
      success: true,
      hungerRestored: hungerGain,
      happinessGain: 5
    };
  }

  createCustomMeal(pet, ingredients) {
    return {
      id: 'custom_meal',
      name: 'Custom Meal',
      effectiveness: 30,
      ingredients
    };
  }
}

module.exports = PetTrainingSystem;