/**
 * Comprehensive pet care system with feeding, grooming, training,
 * bonding activities, and housing management
 */

class PetCare {
  constructor(petDatabase, world) {
    this.petDatabase = petDatabase;
    this.world = world;
    this.careSchedules = new Map();
    this.housingSystem = new PetHousingSystem();
    this.trainingSystem = new PetTrainingSystem();
    this.groomingSystem = new PetGroomingSystem();
    this.feedingSystem = new PetFeedingSystem();
    this.bondingActivities = new Map();
    this.careHistory = new Map();
    this.autoCareSettings = new Map();
  }

  // MAIN CARE INTERFACE
  performCareAction(pet, actionType, params = {}) {
    const actionHandlers = {
      feed: () => this.feedingSystem.feedPet(pet, params.food, params.amount),
      groom: () => this.groomingSystem.groomPet(pet, params.method, params.tools),
      train: () => this.trainingSystem.trainPet(pet, params.skill, params.intensity),
      play: () => this.performPlayActivity(pet, params.activity, params.duration),
      heal: () => this.healPet(pet, params.method, params.items),
      exercise: () => this.exercisePet(pet, params.activity, params.intensity),
      socialize: () => this.socializePet(pet, params.target, params.activity),
      rest: () => this.restPet(pet, params.location, params.duration),
      bath: () => this.bathePet(pet, params.products, params.temperature)
    };

    const handler = actionHandlers[actionType];
    if (!handler) {
      return { success: false, reason: 'invalid_care_action' };
    }

    try {
      const result = handler();

      // Record care action
      this.recordCareAction(pet, actionType, params, result);

      // Update pet status
      this.updatePetCareStatus(pet, actionType, result);

      // Generate care memory
      this.generateCareMemory(pet, actionType, result);

      return result;
    } catch (error) {
      return {
        success: false,
        reason: 'care_action_failed',
        error: error.message
      };
    }
  }

  recordCareAction(pet, actionType, params, result) {
    if (!this.careHistory.has(pet.id)) {
      this.careHistory.set(pet.id, []);
    }

    const history = this.careHistory.get(pet.id);
    history.push({
      actionType,
      params,
      result,
      timestamp: Date.now(),
      performer: params.performer || 'owner',
      location: params.location || pet.currentLocation
    });

    // Keep only last 100 care actions
    if (history.length > 100) {
      history.shift();
    }
  }

  updatePetCareStatus(pet, actionType, result) {
    if (result.success) {
      // Update last care times
      switch (actionType) {
        case 'feed':
          pet.lastFed = Date.now();
          break;
        case 'groom':
        case 'bath':
          pet.lastGroomed = Date.now();
          break;
        case 'train':
          pet.lastTrained = Date.now();
          break;
        case 'play':
        case 'socialize':
          pet.lastPlayed = Date.now();
          break;
        case 'rest':
          pet.lastRested = Date.now();
          break;
      }

      // Update care streaks
      this.updateCareStreaks(pet, actionType);
    }
  }

  updateCareStreaks(pet, actionType) {
    const today = new Date().toDateString();

    if (!pet.careStreaks) {
      pet.careStreaks = {};
    }

    if (!pet.careStreaks[actionType]) {
      pet.careStreaks[actionType] = { current: 0, lastDate: null, best: 0 };
    }

    const streak = pet.careStreaks[actionType];

    if (streak.lastDate === today) {
      // Already did this action today
      return;
    }

    const yesterday = new Date(Date.now() - 86400000).toDateString();
    if (streak.lastDate === yesterday) {
      // Continue streak
      streak.current++;
    } else {
      // Start new streak
      streak.current = 1;
    }

    streak.lastDate = today;
    streak.best = Math.max(streak.best, streak.current);
  }

  generateCareMemory(pet, actionType, result) {
    const memoryImportance = this.calculateMemoryImportance(actionType, result);
    const memoryContent = this.generateMemoryContent(actionType, result);

    pet.addMemory({
      type: 'care_action',
      content: memoryContent,
      importance: memoryImportance,
      actionType,
      success: result.success
    });
  }

  calculateMemoryImportance(actionType, result) {
    const baseImportance = {
      feed: 1,
      groom: 1,
      train: 2,
      play: 2,
      heal: 3,
      exercise: 1,
      socialize: 2,
      rest: 1,
      bath: 1
    };

    let importance = baseImportance[actionType] || 1;

    // Increase importance for successful actions
    if (result.success) {
      importance += 0.5;
    }

    // Increase importance for actions with significant effects
    if (result.bondingIncrease > 5) {
      importance += 1;
    }

    if (result.significantChanges) {
      importance += 1;
    }

    return Math.min(5, Math.floor(importance));
  }

  generateMemoryContent(actionType, result) {
    const templates = {
      feed: () => result.success ?
        `Was fed ${result.foodDescription || 'food'} and enjoyed it` :
        `Was offered food but didn't eat well`,
      groom: () => result.success ?
        `Was groomed and feels clean and comfortable` :
        `Grooming session didn't go well`,
      train: () => result.success ?
        `Trained ${result.skillLearned || 'new skills'} and made progress` :
        `Training session was challenging`,
      play: () => result.success ?
        `Played ${result.activity || 'games'} and had fun` :
        `Playtime didn't go as planned`,
      heal: () => result.success ?
        `Received medical treatment and feels better` :
        `Medical treatment was needed`,
      exercise: () => result.success ?
        `Exercised and feels energized` :
        `Exercise session was difficult`,
      socialize: () => result.success ?
        `Socialized with ${result.target || 'others'} and enjoyed it` :
        `Social interaction was challenging`,
      rest: () => result.success ?
        `Rested well and feels refreshed` :
        `Rest was disturbed`,
      bath: () => result.success ?
        `Had a bath and feels sparkling clean` :
        `Bath time was stressful`
    };

    return templates[actionType]?.() || `Care action: ${actionType}`;
  }

  // FEEDING SYSTEM
  getFeedingRecommendations(pet) {
    return this.feedingSystem.getRecommendations(pet);
  }

  getFoodPreferences(pet) {
    return this.feedingSystem.getPreferences(pet);
  }

  createCustomMeal(pet, ingredients) {
    return this.feedingSystem.createCustomMeal(pet, ingredients);
  }

  // GROOMING SYSTEM
  getGroomingNeeds(pet) {
    return this.groomingSystem.getNeeds(pet);
  }

  getAvailableGroomingServices(pet) {
    return this.groomingSystem.getAvailableServices(pet);
  }

  // TRAINING SYSTEM
  getTrainingOptions(pet) {
    return this.trainingSystem.getAvailableTraining(pet);
  }

  createCustomTraining(pet, skills, schedule) {
    return this.trainingSystem.createCustomPlan(pet, skills, schedule);
  }

  // PLAY AND SOCIAL ACTIVITIES
  performPlayActivity(pet, activity, duration = 30) {
    const playActivities = this.getPlayActivities(pet);
    const selectedActivity = playActivities.find(a => a.id === activity) || playActivities[0];

    if (!selectedActivity) {
      return { success: false, reason: 'activity_not_available' };
    }

    // Check energy requirements
    const energyCost = this.calculateActivityEnergyCost(selectedActivity, duration);
    if (pet.energy < energyCost) {
      return { success: false, reason: 'insufficient_energy', required: energyCost };
    }

    // Execute play activity
    const result = this.executePlayActivity(pet, selectedActivity, duration);

    return result;
  }

  getPlayActivities(pet) {
    const baseActivities = [
      {
        id: 'fetch',
        name: 'Fetch',
        description: 'Play fetch with toys or objects',
        energyCost: 15,
        happinessGain: 20,
        bondingGain: 8,
        skillsGained: ['agility'],
        suitableFor: ['dog', 'wolf', 'animal'],
        requirements: { space: 'medium', toy: 'ball' }
      },
      {
        id: 'chase',
        name: 'Chase Games',
        description: 'Chase games and tag',
        energyCost: 20,
        happinessGain: 25,
        bondingGain: 10,
        skillsGained: ['speed', 'agility'],
        suitableFor: ['cat', 'animal', 'young'],
        requirements: { space: 'large' }
      },
      {
        id: 'puzzle',
        name: 'Puzzle Games',
        description: 'Mental stimulation through puzzles',
        energyCost: 10,
        happinessGain: 15,
        bondingGain: 5,
        skillsGained: ['intelligence'],
        suitableFor: ['all'],
        requirements: { items: 'puzzle_toys' }
      },
      {
        id: 'hide_and_seek',
        name: 'Hide and Seek',
        description: 'Hide and seek games',
        energyCost: 18,
        happinessGain: 22,
        bondingGain: 12,
        skillsGained: ['stealth', 'perception'],
        suitableFor: ['animal', 'young'],
        requirements: { space: 'large', obstacles: true }
      },
      {
        id: 'training_games',
        name: 'Training Games',
        description: 'Fun training exercises',
        energyCost: 12,
        happinessGain: 18,
        bondingGain: 10,
        skillsGained: ['obedience', 'skills'],
        suitableFor: ['all'],
        requirements: { treats: true }
      },
      {
        id: 'exploration',
        name: 'Exploration',
        description: 'Explore new areas together',
        energyCost: 25,
        happinessGain: 30,
        bondingGain: 15,
        skillsGained: ['exploration', 'courage'],
        suitableFor: ['curious', 'adventurous'],
        requirements: { environment: 'safe_outdoor' }
      },
      {
        id: 'magic_games',
        name: 'Magic Games',
        description: 'Magical play activities',
        energyCost: 20,
        happinessGain: 25,
        bondingGain: 8,
        skillsGained: ['magic_control', 'spell_practice'],
        suitableFor: ['magical', 'elemental'],
        requirements: { magic_level: 'basic' }
      },
      {
        id: 'social_play',
        name: 'Social Play',
        description: 'Play with other pets',
        energyCost: 22,
        happinessGain: 28,
        bondingGain: 5,
        skillsGained: ['social_skills'],
        suitableFor: ['social', 'friendly'],
        requirements: { other_pets: true }
      }
    ];

    // Filter activities suitable for this pet
    return baseActivities.filter(activity =>
      this.isActivitySuitable(pet, activity)
    );
  }

  isActivitySuitable(pet, activity) {
    // Check if activity is suitable for pet type/traits
    if (activity.suitableFor.includes('all')) return true;

    // Check pet category
    if (activity.suitableFor.includes(pet.category)) return true;

    // Check pet traits
    for (const trait of activity.suitableFor) {
      if (pet.traits.includes(trait) || pet.personality.primary === trait) {
        return true;
      }
    }

    // Check age/evolution stage
    if (activity.suitableFor.includes('young') && pet.evolutionStage <= 1) return true;

    return false;
  }

  calculateActivityEnergyCost(activity, duration) {
    const baseCost = activity.energyCost || 10;
    const durationMultiplier = duration / 30; // Base is 30 minutes
    const intensityMultiplier = activity.intensity || 1.0;

    return Math.floor(baseCost * durationMultiplier * intensityMultiplier);
  }

  executePlayActivity(pet, activity, duration) {
    const energyCost = this.calculateActivityEnergyCost(activity, duration);

    // Consume energy
    pet.energy = Math.max(0, pet.energy - energyCost);

    // Calculate gains
    const happinessGain = this.calculateGain(activity.happinessGain, pet.personality, 'happiness');
    const bondingGain = this.calculateGain(activity.bondingGain, pet.personality, 'bonding');

    // Apply gains
    pet.happiness = Math.min(100, pet.happiness + happinessGain);
    pet.bonding = Math.min(100, pet.bonding + bondingGain);

    // Gain experience
    const experienceGain = Math.floor(energyCost / 2);
    pet.gainExperience(experienceGain);

    // Learn skills
    const skillsLearned = [];
    if (activity.skillsGained) {
      for (const skill of activity.skillsGained) {
        if (Math.random() < 0.3) { // 30% chance to learn each skill
          pet.learnBehavior(skill);
          skillsLearned.push(skill);
        }
      }
    }

    // Check for special events
    const specialEvents = this.checkForSpecialPlayEvents(pet, activity);

    return {
      success: true,
      activity: activity.name,
      duration,
      energyCost,
      happinessGain,
      bondingGain,
      experienceGain,
      skillsLearned,
      specialEvents,
      description: `Played ${activity.name} for ${duration} minutes`
    };
  }

  calculateGain(baseGain, personality, gainType) {
    let multiplier = 1.0;

    // Personality-based modifiers
    switch (personality.primary) {
      case 'playful':
        if (gainType === 'happiness') multiplier = 1.3;
        break;
      case 'affectionate':
        if (gainType === 'bonding') multiplier = 1.4;
        break;
      case 'energetic':
        multiplier = 1.2;
        break;
      case 'lazy':
        multiplier = 0.8;
        break;
    }

    // Mood modifier
    multiplier *= pet.moodModifier;

    // Add some randomness
    const randomFactor = 0.8 + Math.random() * 0.4; // 80-120%

    return Math.floor(baseGain * multiplier * randomFactor);
  }

  checkForSpecialPlayEvents(pet, activity) {
    const events = [];

    // Check for bonding milestones
    if (pet.bonding >= 80 && !pet.eventFlags.high_bonding_celebrated) {
      events.push({
        type: 'bonding_milestone',
        description: 'Achieved high bonding level!',
        reward: { bonding: 5, happiness: 10 }
      });
      pet.eventFlags.high_bonding_celebrated = true;
    }

    // Check for perfect mood
    if (pet.currentEmotion === 'ecstatic' && Math.random() < 0.1) {
      events.push({
        type: 'perfect_moment',
        description: 'Perfect moment of joy!',
        reward: { experience: 25 }
      });
    }

    // Check for skill breakthrough
    if (activity.skillsGained && Math.random() < 0.05) {
      events.push({
        type: 'skill_breakthrough',
        description: 'Skill breakthrough!',
        reward: { skillPoints: 1 }
      });
    }

    return events;
  }

  socializePet(pet, target, activity = 'interaction') {
    if (!target) {
      return { success: false, reason: 'no_target' };
    }

    // Check if target is available for socializing
    if (!this.isTargetAvailable(target)) {
      return { success: false, reason: 'target_unavailable' };
    }

    // Calculate social compatibility
    const compatibility = this.calculateSocialCompatibility(pet, target);
    const successChance = 0.7 + (compatibility * 0.3);

    if (Math.random() > successChance) {
      return {
        success: false,
        reason: 'social_interaction_failed',
        compatibility
      };
    }

    // Perform social interaction
    const result = this.executeSocialInteraction(pet, target, activity, compatibility);

    return result;
  }

  isTargetAvailable(target) {
    // Check if target is available for socializing
    if (target.currentHealth <= 0) return false;
    if (target.energy < 20) return false;
    if (target.currentEmotion === 'angry' || target.currentEmotion === 'fearful') return false;

    return true;
  }

  calculateSocialCompatibility(pet, target) {
    let compatibility = 0.5; // Base compatibility

    // Same species bonus
    if (pet.typeId === target.typeId) {
      compatibility += 0.2;
    }

    // Same category bonus
    if (pet.category === target.category) {
      compatibility += 0.1;
    }

    // Personality compatibility
    const personalityCompatibility = this.calculatePersonalityCompatibility(pet.personality, target.personality);
    compatibility += personalityCompatibility * 0.2;

    // Mood compatibility
    const moodCompatibility = this.calculateMoodCompatibility(pet.currentEmotion, target.currentEmotion);
    compatibility += moodCompatibility * 0.1;

    // Past interactions
    const pastInteractionBonus = this.getPastInteractionBonus(pet, target);
    compatibility += pastInteractionBonus;

    return Math.max(0, Math.min(1, compatibility));
  }

  calculatePersonalityCompatibility(personality1, personality2) {
    const compatible = {
      playful: ['playful', 'energetic', 'curious'],
      affectionate: ['affectionate', 'gentle', 'loyal'],
      loyal: ['loyal', 'protective', 'affectionate'],
      curious: ['curious', 'playful', 'adventurous'],
      gentle: ['gentle', 'affectionate', 'calm'],
      independent: ['independent', 'curious', 'cautious']
    };

    const p1 = personality1.primary;
    const p2 = personality2.primary;

    if (compatible[p1]?.includes(p2) || compatible[p2]?.includes(p1)) {
      return 0.8;
    }

    // Check for incompatible personalities
    const incompatible = {
      timid: ['aggressive', 'dominant'],
      lazy: ['energetic', 'aggressive'],
      aggressive: ['timid', 'gentle']
    };

    if (incompatible[p1]?.includes(p2) || incompatible[p2]?.includes(p1)) {
      return -0.3;
    }

    return 0.2; // Neutral compatibility
  }

  calculateMoodCompatibility(emotion1, emotion2) {
    const positiveEmotions = ['happy', 'ecstatic', 'excited', 'loving'];
    const negativeEmotions = ['sad', 'angry', 'fearful', 'anxious'];

    // Both positive = good compatibility
    if (positiveEmotions.includes(emotion1) && positiveEmotions.includes(emotion2)) {
      return 0.6;
    }

    // Both negative = some compatibility
    if (negativeEmotions.includes(emotion1) && negativeEmotions.includes(emotion2)) {
      return 0.3;
    }

    // Mixed emotions = neutral compatibility
    return 0.0;
  }

  getPastInteractionBonus(pet, target) {
    // Check past interactions between pets
    const petHistory = this.careHistory.get(pet.id) || [];
    const pastInteractions = petHistory.filter(action =>
      action.actionType === 'socialize' &&
      action.params.target?.id === target.id
    );

    if (pastInteractions.length === 0) return 0;

    // Calculate based on success rate
    const successfulInteractions = pastInteractions.filter(action => action.result.success);
    const successRate = successfulInteractions.length / pastInteractions.length;

    return successRate * 0.2; // Max 0.2 bonus from past interactions
  }

  executeSocialInteraction(pet, target, activity, compatibility) {
    const energyCost = 10;
    const interactionStrength = compatibility;

    // Energy cost for both pets
    pet.energy = Math.max(0, pet.energy - energyCost);
    if (target.energy) {
      target.energy = Math.max(0, target.energy - energyCost);
    }

    // Calculate benefits
    const happinessGain = Math.floor(10 * interactionStrength);
    const bondingGain = Math.floor(5 * interactionStrength);

    // Apply to both pets
    pet.happiness = Math.min(100, pet.happiness + happinessGain);
    pet.bonding = Math.min(100, pet.bonding + bondingGain);

    if (target.happiness && target.bonding) {
      target.happiness = Math.min(100, target.happiness + Math.floor(happinessGain * 0.7));
      // Note: target.bonding is with their owner, not this pet
    }

    // Create social memory
    pet.addMemory({
      type: 'social_interaction',
      content: `Socialized with ${target.name}`,
      importance: 2
    });

    if (target.addMemory) {
      target.addMemory({
        type: 'social_interaction',
        content: `Socialized with ${pet.name}`,
        importance: 2
      });
    }

    // Check for friendship development
    const friendshipLevel = this.developFriendship(pet, target, interactionStrength);

    return {
      success: true,
      activity,
      target: target.name,
      compatibility,
      happinessGain,
      bondingGain,
      friendshipLevel,
      description: `Socialized with ${target.name} via ${activity}`
    };
  }

  developFriendship(pet, target, interactionStrength) {
    // Simple friendship tracking
    if (!pet.friendships) {
      pet.friendships = new Map();
    }

    const currentLevel = pet.friendships.get(target.id) || 0;
    const newLevel = Math.min(100, currentLevel + Math.floor(interactionStrength * 10));

    pet.friendships.set(target.id, newLevel);

    // Determine friendship level
    if (newLevel >= 80) return 'best_friends';
    if (newLevel >= 60) return 'close_friends';
    if (newLevel >= 40) return 'friends';
    if (newLevel >= 20) return 'acquaintances';
    return 'strangers';
  }

  // HEALTH AND HEALING
  healPet(pet, method = 'rest', items = []) {
    const healingMethods = {
      rest: { effectiveness: 0.5, energyCost: 0 },
      potion: { effectiveness: 0.8, energyCost: 5 },
      magic: { effectiveness: 0.9, energyCost: 15 },
      medical: { effectiveness: 0.95, energyCost: 10 },
      food: { effectiveness: 0.3, energyCost: 5 }
    };

    const selectedMethod = healingMethods[method] || healingMethods.rest;

    if (pet.energy < selectedMethod.energyCost) {
      return { success: false, reason: 'insufficient_energy' };
    }

    // Calculate healing amount
    const maxHeal = pet.maxHealth - pet.currentHealth;
    const healAmount = Math.floor(maxHeal * selectedMethod.effectiveness);

    // Apply healing
    pet.currentHealth = Math.min(pet.maxHealth, pet.currentHealth + healAmount);
    pet.energy = Math.max(0, pet.energy - selectedMethod.energyCost);

    // Add healing memory
    pet.addMemory({
      type: 'healing',
      content: `Received ${method} treatment`,
      importance: healAmount > 50 ? 3 : 2
    });

    return {
      success: true,
      method,
      amountHealed: healAmount,
      currentHealth: pet.currentHealth,
      maxHealth: pet.maxHealth
    };
  }

  // EXERCISE SYSTEM
  exercisePet(pet, activity, intensity = 'moderate') {
    const exerciseActivities = {
      walk: { energyCost: 15, healthBenefit: 10, happinessBenefit: 8 },
      run: { energyCost: 25, healthBenefit: 20, happinessBenefit: 15 },
      swim: { energyCost: 20, healthBenefit: 18, happinessBenefit: 12 },
      climb: { energyCost: 22, healthBenefit: 15, happinessBenefit: 10 },
      fly: { energyCost: 30, healthBenefit: 25, happinessBenefit: 20 },
      strength: { energyCost: 25, healthBenefit: 22, happinessBenefit: 5 },
      agility: { energyCost: 20, healthBenefit: 15, happinessBenefit: 18 }
    };

    const selectedExercise = exerciseActivities[activity];
    if (!selectedExercise) {
      return { success: false, reason: 'invalid_exercise' };
    }

    const intensityMultiplier = { light: 0.7, moderate: 1.0, intense: 1.3 }[intensity] || 1.0;
    const totalEnergyCost = Math.floor(selectedExercise.energyCost * intensityMultiplier);

    if (pet.energy < totalEnergyCost) {
      return { success: false, reason: 'insufficient_energy', required: totalEnergyCost };
    }

    // Apply exercise
    pet.energy = Math.max(0, pet.energy - totalEnergyCost);
    pet.happiness = Math.min(100, pet.happiness + Math.floor(selectedExercise.happinessBenefit * intensityMultiplier));

    // Health benefits
    const healthBenefit = Math.floor(selectedExercise.healthBenefit * intensityMultiplier);
    pet.currentHealth = Math.min(pet.maxHealth, pet.currentHealth + healthBenefit);

    // Stats improvement over time
    this.improveStatsThroughExercise(pet, activity, intensity);

    return {
      success: true,
      activity,
      intensity,
      energyCost: totalEnergyCost,
      healthBenefit,
      happinessBenefit: Math.floor(selectedExercise.happinessBenefit * intensityMultiplier)
    };
  }

  improveStatsThroughExercise(pet, activity, intensity) {
    const statImprovements = {
      walk: { speed: 0.1, endurance: 0.2 },
      run: { speed: 0.3, endurance: 0.4 },
      swim: { endurance: 0.3, health: 0.2 },
      climb: { strength: 0.2, agility: 0.3 },
      fly: { agility: 0.4, endurance: 0.3 },
      strength: { strength: 0.5, health: 0.2 },
      agility: { agility: 0.4, speed: 0.2 }
    };

    const improvements = statImprovements[activity] || {};
    const intensityMultiplier = { light: 0.5, moderate: 1.0, intense: 1.5 }[intensity] || 1.0;

    for (const [stat, improvement] of Object.entries(improvements)) {
      if (Math.random() < 0.1) { // 10% chance per exercise session
        const actualImprovement = improvement * intensityMultiplier;
        pet.stats[stat] = Math.floor(pet.stats[stat] + actualImprovement);
      }
    }
  }

  // REST SYSTEM
  restPet(pet, location = 'current', duration = 60) {
    const restLocations = {
      current: { comfort: 0.5, safety: 0.7 },
      home: { comfort: 0.9, safety: 1.0 },
      bed: { comfort: 1.0, safety: 0.9 },
      safe_spot: { comfort: 0.7, safety: 1.0 },
      natural: { comfort: 0.6, safety: 0.6 }
    };

    const locationBonus = restLocations[location] || restLocations.current;
    const durationMultiplier = Math.min(2.0, duration / 60); // Max 2x for 2+ hours

    // Calculate energy restoration
    const energyRestored = Math.floor(
      50 * locationBonus.comfort * durationMultiplier
    );
    pet.energy = Math.min(100, pet.energy + energyRestored);

    // Health restoration
    const healthRestored = Math.floor(
      10 * locationBonus.safety * durationMultiplier
    );
    pet.currentHealth = Math.min(pet.maxHealth, pet.currentHealth + healthRestored);

    // Happiness improvement
    if (locationBonus.comfort > 0.7) {
      pet.happiness = Math.min(100, pet.happiness + Math.floor(5 * durationMultiplier));
    }

    return {
      success: true,
      location,
      duration,
      energyRestored,
      healthRestored,
      comfortLevel: locationBonus.comfort
    };
  }

  // BATHING SYSTEM
  bathePet(pet, products = [], temperature = 'warm') {
    const temperatureComfort = {
      cold: 0.3,
      cool: 0.6,
      warm: 1.0,
      hot: 0.4
    };

    const comfortLevel = temperatureComfort[temperature] || 0.5;

    if (pet.traits.includes('water_afraid')) {
      return {
        success: false,
        reason: 'water_fear',
        suggestion: 'try dry bathing or gradual water introduction'
      };
    }

    // Calculate cleanliness improvement
    const cleanlinessGain = Math.floor(40 * comfortLevel);
    pet.cleanliness = Math.min(100, pet.cleanliness + cleanlinessGain);

    // Happiness effect based on pet personality
    let happinessEffect = 0;
    if (pet.personality.primary === 'affectionate') {
      happinessEffect = Math.floor(10 * comfortLevel);
    } else if (pet.personality.primary === 'independent') {
      happinessEffect = Math.floor(-5 * (1 - comfortLevel));
    }

    pet.happiness = Math.max(0, Math.min(100, pet.happiness + happinessEffect));

    // Apply product effects
    const productEffects = this.applyBathingProducts(pet, products);

    pet.lastGroomed = Date.now();

    return {
      success: true,
      temperature,
      cleanlinessGain,
      happinessEffect,
      productEffects,
      comfortLevel
    };
  }

  applyBathingProducts(pet, products) {
    const effects = [];

    for (const product of products) {
      switch (product.type) {
        case 'shampoo':
          pet.cleanliness = Math.min(100, pet.cleanliness + 10);
          effects.push('clean_coat');
          break;
        case 'conditioner':
          pet.traits.push('soft_coat');
          effects.push('soft_coat');
          break;
        case 'flea_treatment':
          pet.traits.push('pest_free');
          effects.push('pest_protection');
          break;
        case 'fragrance':
          pet.traits.push('pleasant_scent');
          effects.push('pleasant_scent');
          break;
        case 'medicated':
          pet.currentHealth = Math.min(pet.maxHealth, pet.currentHealth + 15);
          effects.push('health_boost');
          break;
      }
    }

    return effects;
  }

  // AUTO-CARE SYSTEM
  setupAutoCare(petId, settings) {
    const autoCare = {
      feeding: {
        enabled: settings.feeding?.enabled || false,
        schedule: settings.feeding?.schedule || ['08:00', '20:00'],
        foods: settings.feeding?.foods || ['auto_select'],
        threshold: settings.feeding?.threshold || 30
      },
      grooming: {
        enabled: settings.grooming?.enabled || false,
        frequency: settings.grooming?.frequency || 'daily',
        threshold: settings.grooming?.threshold || 40
      },
      exercise: {
        enabled: settings.exercise?.enabled || false,
        frequency: settings.exercise?.frequency || 'daily',
        intensity: settings.exercise?.intensity || 'moderate',
        threshold: settings.exercise?.threshold || 50
      },
      play: {
        enabled: settings.play?.enabled || false,
        frequency: settings.play?.frequency || 'daily',
        duration: settings.play?.duration || 30,
        threshold: settings.play?.threshold || 60
      },
      rest: {
        enabled: settings.rest?.enabled || false,
        schedule: settings.rest?.schedule || ['22:00'],
        duration: settings.rest?.duration || 120
      }
    };

    this.autoCareSettings.set(petId, autoCare);

    return { success: true, autoCare };
  }

  processAutoCare() {
    const now = new Date();
    const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

    for (const [petId, autoCare] of this.autoCareSettings.entries()) {
      const pet = this.getPetById(petId);
      if (!pet || !this.isAutoCareAllowed(pet)) continue;

      this.processAutoCareForPet(pet, autoCare, currentTime, now);
    }
  }

  isAutoCareAllowed(pet) {
    // Don't auto-care if pet is in combat, being manually cared for, etc.
    if (pet.combatState) return false;
    if (pet.currentHealth <= 0) return false;
    if (pet.currentEmotion === 'angry' || pet.currentEmotion === 'fearful') return false;

    return true;
  }

  processAutoCareForPet(pet, autoCare, currentTime, now) {
    // Feeding
    if (autoCare.feeding.enabled && this.shouldPerformAutoCare(autoCare.feeding, currentTime, pet.hunger, 'less_than')) {
      this.performAutoFeeding(pet, autoCare.feeding);
    }

    // Grooming
    if (autoCare.grooming.enabled && this.shouldPerformAutoCare(autoCare.grooming, now, pet.cleanliness, 'less_than')) {
      this.performAutoGrooming(pet, autoCare.grooming);
    }

    // Exercise
    if (autoCare.exercise.enabled && this.shouldPerformAutoCare(autoCare.exercise, now, pet.energy, 'greater_than')) {
      this.performAutoExercise(pet, autoCare.exercise);
    }

    // Play
    if (autoCare.play.enabled && this.shouldPerformAutoCare(autoCare.play, now, pet.happiness, 'less_than')) {
      this.performAutoPlay(pet, autoCare.play);
    }

    // Rest
    if (autoCare.rest.enabled && autoCare.rest.schedule.includes(currentTime)) {
      this.performAutoRest(pet, autoCare.rest);
    }
  }

  shouldPerformAutoCare(careSetting, currentTime, currentValue, comparison) {
    if (careSetting.schedule) {
      return careSetting.schedule.includes(currentTime);
    }

    if (careSetting.frequency === 'daily') {
      const lastCare = this.getLastAutoCareTime(careSetting);
      const hoursSinceLast = (Date.now() - lastCare) / (1000 * 60 * 60);
      return hoursSinceLast >= 24;
    }

    // Threshold-based care
    if (comparison === 'less_than') {
      return currentValue < careSetting.threshold;
    } else if (comparison === 'greater_than') {
      return currentValue > careSetting.threshold;
    }

    return false;
  }

  getLastAutoCareTime(careSetting) {
    return careSetting.lastPerformed || 0;
  }

  performAutoFeeding(pet, feedingSettings) {
    // Auto-feeding implementation
    const food = this.selectBestAutoFood(pet, feedingSettings.foods);
    if (food) {
      this.performCareAction(pet, 'feed', { food, amount: 'auto', performer: 'auto_care' });
      feedingSettings.lastPerformed = Date.now();
    }
  }

  performAutoGrooming(pet, groomingSettings) {
    this.performCareAction(pet, 'groom', { method: 'auto', tools: 'auto', performer: 'auto_care' });
    groomingSettings.lastPerformed = Date.now();
  }

  performAutoExercise(pet, exerciseSettings) {
    const activities = ['walk', 'run', 'play'];
    const activity = activities[Math.floor(Math.random() * activities.length)];
    this.performCareAction(pet, 'exercise', { activity, intensity: exerciseSettings.intensity, performer: 'auto_care' });
    exerciseSettings.lastPerformed = Date.now();
  }

  performAutoPlay(pet, playSettings) {
    const activities = this.getPlayActivities(pet);
    const activity = activities[0]?.id || 'fetch';
    this.performCareAction(pet, 'play', { activity, duration: playSettings.duration, performer: 'auto_care' });
    playSettings.lastPerformed = Date.now();
  }

  performAutoRest(pet, restSettings) {
    this.performCareAction(pet, 'rest', { location: 'auto', duration: restSettings.duration, performer: 'auto_care' });
    restSettings.lastPerformed = Date.now();
  }

  selectBestAutoFood(pet, foodPreferences) {
    // Implementation for auto-selecting best food
    return 'auto_food'; // Placeholder
  }

  getPetById(petId) {
    // This would interface with the pet management system
    return null; // Placeholder
  }

  // CARE ANALYTICS
  getCareReport(petId, timeRange = 7) {
    const history = this.careHistory.get(petId) || [];
    const cutoffTime = Date.now() - (timeRange * 24 * 60 * 60 * 1000);
    const recentHistory = history.filter(action => action.timestamp > cutoffTime);

    const report = {
      timeRangeDays: timeRange,
      totalActions: recentHistory.length,
      actionBreakdown: this.calculateActionBreakdown(recentHistory),
      successRate: this.calculateSuccessRate(recentHistory),
      careStreaks: this.getCareStreaks(petId),
      recommendations: this.generateCareRecommendations(petId, recentHistory),
      moodTrends: this.calculateMoodTrends(recentHistory),
      healthTrends: this.calculateHealthTrends(recentHistory)
    };

    return report;
  }

  calculateActionBreakdown(history) {
    const breakdown = {};
    for (const action of history) {
      breakdown[action.actionType] = (breakdown[action.actionType] || 0) + 1;
    }
    return breakdown;
  }

  calculateSuccessRate(history) {
    if (history.length === 0) return 0;
    const successful = history.filter(action => action.result.success).length;
    return (successful / history.length) * 100;
  }

  getCareStreaks(petId) {
    const pet = this.getPetById(petId);
    return pet?.careStreaks || {};
  }

  generateCareRecommendations(petId, history) {
    const recommendations = [];
    const pet = this.getPetById(petId);

    if (!pet) return recommendations;

    // Analyze recent care patterns
    const lastFed = history.filter(a => a.actionType === 'feed').pop();
    if (!lastFed || Date.now() - lastFed.timestamp > 12 * 60 * 60 * 1000) {
      recommendations.push({
        type: 'feeding',
        priority: 'high',
        message: 'Pet hasn\'t been fed recently',
        suggestedAction: 'feed'
      });
    }

    if (pet.happiness < 50) {
      recommendations.push({
        type: 'happiness',
        priority: 'medium',
        message: 'Pet happiness is low',
        suggestedAction: 'play'
      });
    }

    if (pet.cleanliness < 40) {
      recommendations.push({
        type: 'grooming',
        priority: 'medium',
        message: 'Pet needs grooming',
        suggestedAction: 'groom'
      });
    }

    return recommendations;
  }

  calculateMoodTrends(history) {
    // Implementation for mood trend analysis
    return { improving: true, stable: false };
  }

  calculateHealthTrends(history) {
    // Implementation for health trend analysis
    return { improving: true, stable: true };
  }
}

// HOUSING SYSTEM
class PetHousingSystem {
  constructor() {
    this.habitats = new Map();
    this.decorations = new Map();
    this.housingUpgrades = new Map();
  }

  createHabitat(petId, habitatType, location) {
    const habitat = {
      id: this.generateHabitatId(),
      petId,
      type: habitatType,
      location,
      level: 1,
      comfort: 50,
      space: 100,
      cleanliness: 80,
      decorations: [],
      amenities: [],
      occupants: [petId],
      createdAt: Date.now(),
      lastCleaned: Date.now()
    };

    this.habitats.set(habitat.id, habitat);

    return { success: true, habitat };
  }

  upgradeHabitat(habitatId, upgradeType) {
    const habitat = this.habitats.get(habitatId);
    if (!habitat) {
      return { success: false, reason: 'habitat_not_found' };
    }

    const upgrades = {
      comfort: { cost: 500, effect: 15, description: 'Increase comfort level' },
      space: { cost: 800, effect: 50, description: 'Expand living space' },
      cleanliness: { cost: 300, effect: 20, description: 'Improve cleanliness system' },
      amenities: { cost: 1000, effect: 'new_amenity', description: 'Add new amenity' }
    };

    const upgrade = upgrades[upgradeType];
    if (!upgrade) {
      return { success: false, reason: 'invalid_upgrade' };
    }

    // Apply upgrade
    switch (upgradeType) {
      case 'comfort':
        habitat.comfort = Math.min(100, habitat.comfort + upgrade.effect);
        break;
      case 'space':
        habitat.space += upgrade.effect;
        break;
      case 'cleanliness':
        habitat.cleanliness = Math.min(100, habitat.cleanliness + upgrade.effect);
        break;
      case 'amenities':
        habitat.amenities.push('new_amenity');
        break;
    }

    habitat.level++;

    return { success: true, habitat, upgrade };
  }

  addDecoration(habitatId, decoration) {
    const habitat = this.habitats.get(habitatId);
    if (!habitat) {
      return { success: false, reason: 'habitat_not_found' };
    }

    // Check space availability
    const decorationSpace = decoration.space || 10;
    if (this.calculateUsedSpace(habitat) + decorationSpace > habitat.space) {
      return { success: false, reason: 'insufficient_space' };
    }

    habitat.decorations.push(decoration);

    // Apply decoration effects
    this.applyDecorationEffects(habitat, decoration);

    return { success: true, habitat, decoration };
  }

  calculateUsedSpace(habitat) {
    let usedSpace = 0;
    for (const decoration of habitat.decorations) {
      usedSpace += decoration.space || 10;
    }
    return usedSpace;
  }

  applyDecorationEffects(habitat, decoration) {
    if (decoration.effects) {
      for (const [effect, value] of Object.entries(decoration.effects)) {
        switch (effect) {
          case 'comfort':
            habitat.comfort = Math.min(100, habitat.comfort + value);
            break;
          case 'happiness':
            // This would affect pets in the habitat
            break;
          case 'cleanliness':
            habitat.cleanliness = Math.min(100, habitat.cleanliness + value);
            break;
        }
      }
    }
  }

  cleanHabitat(habitatId) {
    const habitat = this.habitats.get(habitatId);
    if (!habitat) {
      return { success: false, reason: 'habitat_not_found' };
    }

    habitat.cleanliness = 100;
    habitat.lastCleaned = Date.now();

    // Positive effect on pets in habitat
    for (const petId of habitat.occupants) {
      const pet = this.getPetById(petId);
      if (pet) {
        pet.happiness = Math.min(100, pet.happiness + 10);
        pet.cleanliness = Math.min(100, pet.cleanliness + 20);
      }
    }

    return { success: true, habitat };
  }

  getHabitatStatus(habitatId) {
    const habitat = this.habitats.get(habitatId);
    if (!habitat) {
      return { success: false, reason: 'habitat_not_found' };
    }

    return {
      success: true,
      habitat: {
        id: habitat.id,
        type: habitat.type,
        level: habitat.level,
        comfort: habitat.comfort,
        cleanliness: habitat.cleanliness,
        space: {
          total: habitat.space,
          used: this.calculateUsedSpace(habitat),
          available: habitat.space - this.calculateUsedSpace(habitat)
        },
        occupants: habitat.occupants.length,
        decorations: habitat.decorations.length,
        amenities: habitat.amenities
      }
    };
  }

  generateHabitatId() {
    return 'habitat_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
  }

  getPetById(petId) {
    // This would interface with the pet management system
    return null; // Placeholder
  }
}

module.exports = PetCare;