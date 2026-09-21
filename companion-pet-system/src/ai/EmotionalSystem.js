/**
 * Advanced emotional system for companion pets
 * Handles complex emotional states, mood transitions, and emotional triggers
 */

class EmotionalSystem {
  constructor(pet) {
    this.pet = pet;
    this.currentEmotion = 'neutral';
    this.emotionIntensity = 0.5;
    this.emotionHistory = [];
    this.emotionTriggers = new Map();
    this.moodStability = 0.7;
    this.emotionalMemory = new Map();
    this.personalityInfluence = this.calculatePersonalityInfluence();
  }

  calculatePersonalityInfluence() {
    const personality = this.pet.personality.primary;
    const influences = {
      // Emotional reactivity (how quickly emotions change)
      reactivity: {
        energetic: 1.5,
        timid: 1.3,
        serious: 0.7,
        lazy: 0.6,
        playful: 1.4,
        affectionate: 1.2
      }[personality] || 1.0,

      // Emotional stability (how long emotions last)
      stability: {
        serious: 1.3,
        lazy: 1.2,
        independent: 1.1,
        timid: 0.8,
        playful: 0.7,
        energetic: 0.6
      }[personality] || 1.0,

      // Social emotional response
      socialResponsiveness: {
        affectionate: 1.5,
        loyal: 1.4,
        gentle: 1.3,
        protective: 1.2,
        independent: 0.7,
        timid: 0.6
      }[personality] || 1.0,

      // Learning from emotional experiences
      emotionalLearning: {
        curious: 1.4,
        intelligent: 1.3,
        wise: 1.2,
        cautious: 1.1,
        lazy: 0.8
      }[personality] || 1.0
    };

    return influences;
  }

  updateEmotion() {
    const newEmotion = this.calculateCurrentEmotion();
    const newIntensity = this.calculateEmotionIntensity();

    // Check if emotion changed
    if (newEmotion !== this.currentEmotion || Math.abs(newIntensity - this.emotionIntensity) > 0.1) {
      this.transitionEmotion(newEmotion, newIntensity);
    }

    // Update emotion history
    this.updateEmotionHistory();

    // Process emotional triggers
    this.processEmotionalTriggers();

    // Apply emotional effects
    this.applyEmotionalEffects();
  }

  calculateCurrentEmotion() {
    const factors = this.getEmotionalFactors();
    let emotionScore = { neutral: 0.5 };

    // Calculate scores for each emotion
    for (const [emotion, factor] of Object.entries(factors)) {
      const score = this.calculateEmotionScore(emotion, factor);
      emotionScore[emotion] = score;
    }

    // Find dominant emotion
    let dominantEmotion = 'neutral';
    let highestScore = 0.5;

    for (const [emotion, score] of Object.entries(emotionScore)) {
      if (score > highestScore) {
        highestScore = score;
        dominantEmotion = emotion;
      }
    }

    return dominantEmotion;
  }

  getEmotionalFactors() {
    return {
      happy: {
        happiness: this.pet.happiness / 100,
        energy: this.pet.energy / 100,
        bonding: this.pet.bonding / 100,
        cleanliness: this.pet.cleanliness / 100
      },
      ecstatic: {
        happiness: (this.pet.happiness - 80) / 20,
        bonding: (this.pet.bonding - 80) / 20,
        energy: (this.pet.energy - 70) / 30
      },
      content: {
        happiness: this.pet.happiness / 100,
        energy: this.pet.energy / 100,
        hunger: this.pet.hunger / 100
      },
      unhappy: {
        happiness: (50 - this.pet.happiness) / 50,
        energy: (50 - this.pet.energy) / 50,
        hunger: (50 - this.pet.hunger) / 50
      },
      sad: {
        happiness: (30 - this.pet.happiness) / 30,
        bonding: (50 - this.pet.bonding) / 50,
        loneliness: this.calculateLoneliness()
      },
      excited: {
        energy: this.pet.energy / 100,
        playfulness: this.calculatePlayfulness(),
        anticipation: this.calculateAnticipation()
      },
      anxious: {
        energy: this.pet.energy / 100,
        uncertainty: this.calculateUncertainty(),
        threat_perception: this.calculateThreatPerception()
      },
      angry: {
        frustration: this.calculateFrustration(),
        threat_perception: this.calculateThreatPerception(),
        hunger_deficit: Math.max(0, (50 - this.pet.hunger) / 50)
      },
      fearful: {
        threat_perception: this.calculateThreatPerception(),
        uncertainty: this.calculateUncertainty(),
        energy_deficit: Math.max(0, (30 - this.pet.energy) / 30)
      },
      loving: {
        bonding: this.pet.bonding / 100,
        affection: this.calculateAffection(),
        trust: this.calculateTrust()
      },
      protective: {
        bonding: this.pet.bonding / 100,
        threat_perception: this.calculateThreatPerception(),
        responsibility: this.calculateResponsibility()
      }
    };
  }

  calculateEmotionScore(emotion, factors) {
    let score = 0;
    let factorCount = 0;

    for (const [factorName, value] of Object.entries(factors)) {
      if (value > 0) {
        score += value;
        factorCount++;
      }
    }

    if (factorCount === 0) return 0;

    const averageScore = score / factorCount;

    // Apply personality modifiers
    const personalityModifier = this.getPersonalityEmotionModifier(emotion);
    const modifiedScore = averageScore * personalityModifier;

    // Apply emotional memory influence
    const memoryInfluence = this.getEmotionalMemoryInfluence(emotion);
    const finalScore = modifiedScore * (1 + memoryInfluence);

    return Math.max(0, Math.min(1, finalScore));
  }

  getPersonalityEmotionModifier(emotion) {
    const personality = this.pet.personality.primary;
    const modifiers = {
      playful: {
        happy: 1.3, ecstatic: 1.4, excited: 1.5,
        sad: 0.7, angry: 0.6
      },
      serious: {
        content: 1.3, protective: 1.2,
        ecstatic: 0.8, excited: 0.7
      },
 timid: {
        fearful: 1.4, anxious: 1.3,
        happy: 0.8, ecstatic: 0.6
      },
      brave: {
        protective: 1.4, happy: 1.2,
        fearful: 0.5, anxious: 0.6
      },
      affectionate: {
        loving: 1.5, happy: 1.3,
        angry: 0.7, sad: 0.8
      },
      independent: {
        content: 1.2, happy: 1.1,
        loving: 0.7, protective: 0.8
      },
      protective: {
        protective: 1.6, anxious: 1.1,
        happy: 0.9, ecstatic: 0.8
      },
      curious: {
        excited: 1.3, happy: 1.2,
        content: 0.9, sad: 0.8
      }
    };

    return modifiers[personality]?.[emotion] || 1.0;
  }

  getEmotionalMemoryInfluence(emotion) {
    const memoryKey = `${emotion}_experience`;
    const memory = this.emotionalMemory.get(memoryKey);

    if (!memory) return 0;

    const age = Date.now() - memory.timestamp;
    const ageDecay = Math.exp(-age / (7 * 24 * 60 * 60 * 1000)); // Decay over a week
    const influence = memory.valence * ageDecay * 0.2; // Max 20% influence

    return influence;
  }

  calculateEmotionIntensity() {
    const factors = this.getEmotionalFactors();
    const currentEmotionFactors = factors[this.currentEmotion] || {};

    let totalIntensity = 0;
    let factorCount = 0;

    for (const [factorName, value] of Object.entries(currentEmotionFactors)) {
      totalIntensity += value;
      factorCount++;
    }

    if (factorCount === 0) return 0.5;

    const baseIntensity = totalIntensity / factorCount;

    // Apply reactivity modifier
    const modifiedIntensity = baseIntensity * this.personalityInfluence.reactivity;

    // Add some randomness for natural variation
    const randomVariation = (Math.random() - 0.5) * 0.1;
    const finalIntensity = Math.max(0.1, Math.min(1.0, modifiedIntensity + randomVariation));

    return finalIntensity;
  }

  // Helper calculation methods
  calculateLoneliness() {
    const timeSinceLastInteraction = Date.now() - (this.pet.lastPlayed || Date.now());
    const hoursSinceLastInteraction = timeSinceLastInteraction / (1000 * 60 * 60);
    return Math.min(1.0, hoursSinceLastInteraction / 24); // Max loneliness after 24 hours
  }

  calculatePlayfulness() {
    const personalityBonus = this.pet.personality.primary === 'playful' ? 0.3 : 0;
    const energyBonus = this.pet.energy / 100 * 0.4;
    const happinessBonus = this.pet.happiness / 100 * 0.3;
    return Math.min(1.0, personalityBonus + energyBonus + happinessBonus);
  }

  calculateAnticipation() {
    // Look for upcoming activities or events
    const hasScheduledActivity = this.checkForScheduledActivities();
    const recentPositiveExperiences = this.checkRecentPositiveExperiences();
    return (hasScheduledActivity ? 0.5 : 0) + (recentPositiveExperiences ? 0.3 : 0);
  }

  calculateUncertainty() {
    // Environmental changes, new situations
    const environmentalChanges = this.checkEnvironmentalChanges();
    const newSituations = this.checkForNewSituations();
    return Math.min(1.0, environmentalChanges + newSituations);
  }

  calculateThreatPerception() {
    // Check for dangers, scary situations
    const obviousThreats = this.checkForThreats();
    const personalityFactor = this.pet.personality.primary === 'timid' ? 1.5 : 1.0;
    return Math.min(1.0, obviousThreats * personalityFactor);
  }

  calculateFrustration() {
    // Failed actions, unmet needs
    const recentFailures = this.checkRecentFailures();
    const unmetNeeds = this.checkUnmetNeeds();
    return Math.min(1.0, recentFailures + unmetNeeds);
  }

  calculateAffection() {
    const bondingLevel = this.pet.bonding / 100;
    const personalityBonus = this.pet.personality.primary === 'affectionate' ? 0.3 : 0;
    const recentPositiveInteractions = this.checkRecentPositiveInteractions();
    return Math.min(1.0, bondingLevel + personalityBonus + recentPositiveInteractions);
  }

  calculateTrust() {
    const bondingLevel = this.pet.bonding / 100;
    const consistentCare = this.checkConsistentCare();
    const positiveMemories = this.countPositiveMemories() / Math.max(1, this.pet.memories.length);
    return Math.min(1.0, (bondingLevel + consistentCare + positiveMemories) / 3);
  }

  calculateResponsibility() {
    const bondingLevel = this.pet.bonding / 100;
    const protectiveInstinct = this.pet.traits.includes('protective') ? 0.3 : 0;
    const maturityBonus = Math.min(0.3, this.pet.level / 100);
    return Math.min(1.0, bondingLevel + protectiveInstinct + maturityBonus);
  }

  // Environment and situation checks
  checkForScheduledActivities() {
    // This would check with the game system for upcoming activities
    return Math.random() < 0.2; // Placeholder
  }

  checkRecentPositiveExperiences() {
    const recentTime = Date.now() - (60 * 60 * 1000); // Last hour
    const positiveMemories = this.pet.memories.filter(memory =>
      memory.timestamp > recentTime &&
      ['happy', 'success', 'reward', 'play'].includes(memory.type)
    );
    return positiveMemories.length > 0;
  }

  checkEnvironmentalChanges() {
    // Check for significant environmental changes
    const currentEnvironment = this.getCurrentEnvironment();
    const lastEnvironment = this.getLastKnownEnvironment();

    if (!lastEnvironment || currentEnvironment.type !== lastEnvironment.type) {
      return 0.8; // High uncertainty in new environment
    }

    return Math.random() * 0.2; // Small random uncertainty
  }

  checkForNewSituations() {
    // Check for new objects, creatures, or situations
    return Math.random() < 0.1 ? 0.5 : 0; // 10% chance of new situation
  }

  checkForThreats() {
    // Check for actual threats in the environment
    const threats = this.identifyThreats();
    return threats.length > 0 ? Math.min(1.0, threats.length * 0.3) : 0;
  }

  checkRecentFailures() {
    const recentTime = Date.now() - (30 * 60 * 1000); // Last 30 minutes
    const failures = this.pet.memories.filter(memory =>
      memory.timestamp > recentTime && memory.type === 'failure'
    );
    return Math.min(1.0, failures.length * 0.2);
  }

  checkUnmetNeeds() {
    const urgentNeeds = [];
    if (this.pet.hunger < 30) urgentNeeds.push('hunger');
    if (this.pet.energy < 30) urgentNeeds.push('energy');
    if (this.pet.happiness < 30) urgentNeeds.push('happiness');
    return Math.min(1.0, urgentNeeds.length * 0.3);
  }

  checkRecentPositiveInteractions() {
    const recentTime = Date.now() - (2 * 60 * 60 * 1000); // Last 2 hours
    const interactions = this.pet.memories.filter(memory =>
      memory.timestamp > recentTime && memory.type === 'pet_interaction'
    );
    return interactions.length > 0 ? 0.3 : 0;
  }

  checkConsistentCare() {
    // Check if care has been consistent over time
    const dayMs = 24 * 60 * 60 * 1000;
    const recentDays = 7;
    const cutoffTime = Date.now() - (recentDays * dayMs);

    const recentMemories = this.pet.memories.filter(memory => memory.timestamp > cutoffTime);
    const careMemories = recentMemories.filter(memory =>
      ['feeding', 'grooming', 'playing', 'healing'].includes(memory.type)
    );

    const expectedCareEvents = recentDays * 3; // Expect 3 care events per day
    const consistencyRatio = careMemories.length / expectedCareEvents;

    return Math.min(1.0, consistencyRatio);
  }

  countPositiveMemories() {
    const positiveTypes = ['happy', 'success', 'reward', 'play', 'affection'];
    return this.pet.memories.filter(memory => positiveTypes.includes(memory.type)).length;
  }

  identifyThreats() {
    // This would check with the world/ai system for actual threats
    return []; // Placeholder
  }

  getCurrentEnvironment() {
    // Get current environment from world system
    return { type: 'forest', weather: 'sunny' }; // Placeholder
  }

  getLastKnownEnvironment() {
    // Get last known environment
    return null; // Placeholder
  }

  transitionEmotion(newEmotion, newIntensity) {
    const oldEmotion = this.currentEmotion;
    const oldIntensity = this.emotionIntensity;

    this.currentEmotion = newEmotion;
    this.emotionIntensity = newIntensity;

    // Add memory of emotion change
    this.pet.addMemory({
      type: 'emotion_change',
      content: `Emotion changed from ${oldEmotion} (${oldIntensity.toFixed(2)}) to ${newEmotion} (${newIntensity.toFixed(2)})`,
      importance: this.calculateEmotionChangeImportance(oldEmotion, newEmotion, oldIntensity, newIntensity)
    });

    // Process emotion transition effects
    this.processEmotionTransitionEffects(oldEmotion, newEmotion);

    // Update emotional memory
    this.updateEmotionalMemory(newEmotion, newIntensity);
  }

  calculateEmotionChangeImportance(oldEmotion, newEmotion, oldIntensity, newIntensity) {
    // Significant emotion changes are more important
    const emotionDifference = oldEmotion !== newEmotion ? 2 : 0;
    const intensityDifference = Math.abs(newIntensity - oldIntensity);

    return Math.min(5, emotionDifference + intensityDifference * 3);
  }

  processEmotionTransitionEffects(oldEmotion, newEmotion) {
    // Positive emotions have beneficial effects
    if (['happy', 'ecstatic', 'loving', 'excited'].includes(newEmotion)) {
      this.pet.happiness = Math.min(100, this.pet.happiness + 5);
      this.pet.energy = Math.min(100, this.pet.energy + 3);
    }

    // Negative emotions have detrimental effects
    if (['sad', 'angry', 'fearful', 'anxious'].includes(newEmotion)) {
      this.pet.happiness = Math.max(0, this.pet.happiness - 3);
      this.pet.energy = Math.max(0, this.pet.energy - 2);
    }

    // Special emotion effects
    switch (newEmotion) {
      case 'ecstatic':
        this.pet.bonding = Math.min(100, this.pet.bonding + 2);
        break;
      case 'protective':
        this.pet.stats.defense = Math.floor(this.pet.stats.defense * 1.1);
        break;
      case 'fearful':
        this.pet.stats.speed = Math.floor(this.pet.stats.speed * 1.1);
        break;
      case 'loving':
        this.pet.bonding = Math.min(100, this.pet.bonding + 5);
        break;
    }
  }

  updateEmotionHistory() {
    this.emotionHistory.push({
      emotion: this.currentEmotion,
      intensity: this.emotionIntensity,
      timestamp: Date.now()
    });

    // Keep only last 100 entries
    if (this.emotionHistory.length > 100) {
      this.emotionHistory.shift();
    }
  }

  processEmotionalTriggers() {
    // Check for specific emotional triggers
    const triggers = this.identifyEmotionalTriggers();

    for (const trigger of triggers) {
      this.processTrigger(trigger);
    }
  }

  identifyEmotionalTriggers() {
    const triggers = [];

    // Environmental triggers
    const environment = this.getCurrentEnvironment();
    if (environment.weather === 'storm' && this.pet.personality.quirks.includes('weather_sensitive')) {
      triggers.push({ type: 'weather_fear', emotion: 'fearful', intensity: 0.7 });
    }

    // Social triggers
    const ownerNearby = this.isOwnerNearby();
    if (ownerNearby && this.pet.personality.primary === 'affectionate') {
      triggers.push({ type: 'owner_presence', emotion: 'happy', intensity: 0.5 });
    }

    // Need-based triggers
    if (this.pet.hunger < 20) {
      triggers.push({ type: 'extreme_hunger', emotion: 'anxious', intensity: 0.8 });
    }

    // Memory-based triggers
    const memoryTriggers = this.checkMemoryTriggers();
    triggers.push(...memoryTriggers);

    return triggers;
  }

  isOwnerNearby() {
    // Check if owner is within interaction range
    return Math.random() < 0.3; // Placeholder
  }

  checkMemoryTriggers() {
    const triggers = [];
    const now = Date.now();
    const recentMemories = this.pet.memories.filter(memory => now - memory.timestamp < 60000); // Last minute

    for (const memory of recentMemories) {
      if (memory.type === 'pet_interaction' && memory.content.includes('successfully')) {
        triggers.push({ type: 'positive_social', emotion: 'happy', intensity: 0.3 });
      }
      if (memory.type === 'failure') {
        triggers.push({ type: 'recent_failure', emotion: 'unhappy', intensity: 0.4 });
      }
    }

    return triggers;
  }

  processTrigger(trigger) {
    // Apply trigger effects
    const triggerKey = `${trigger.type}_${trigger.emotion}`;
    this.emotionTriggers.set(triggerKey, {
      ...trigger,
      processed: Date.now()
    });

    // Add memory of trigger
    this.pet.addMemory({
      type: 'emotional_trigger',
      content: `Triggered ${trigger.emotion} by ${trigger.type}`,
      importance: 2
    });

    // Potentially modify current emotion
    if (trigger.intensity > this.emotionIntensity * 0.5) {
      this.currentEmotion = trigger.emotion;
      this.emotionIntensity = Math.max(this.emotionIntensity, trigger.intensity);
    }
  }

  applyEmotionalEffects() {
    // Apply ongoing emotional effects to pet stats and behavior
    const emotion = this.currentEmotion;
    const intensity = this.emotionIntensity;

    // Apply mood modifier to pet
    this.pet.moodModifier = this.calculateMoodModifier(emotion, intensity);

    // Apply emotional effects to abilities
    this.applyEmotionalAbilityModifiers(emotion, intensity);

    // Influence AI behavior
    this.influenceAIBehavior(emotion, intensity);
  }

  calculateMoodModifier(emotion, intensity) {
    const baseModifiers = {
      ecstatic: 1.3,
      happy: 1.15,
      content: 1.0,
      neutral: 1.0,
      unhappy: 0.85,
      sad: 0.7,
      excited: 1.2,
      anxious: 0.8,
      angry: 0.75,
      fearful: 0.7,
      loving: 1.25,
      protective: 1.1
    };

    const baseModifier = baseModifiers[emotion] || 1.0;
    const intensityFactor = 0.5 + (intensity * 0.5); // Scale with intensity

    return baseModifier * intensityFactor;
  }

  applyEmotionalAbilityModifiers(emotion, intensity) {
    // Modify ability effectiveness based on emotion
    const modifiers = {
      ecstatic: { social: 1.3, play: 1.4 },
      happy: { social: 1.2, train: 1.1 },
      excited: { play: 1.5, explore: 1.3 },
      protective: { combat: 1.4, social: 1.1 },
      fearful: { escape: 1.3, hide: 1.4 },
      angry: { combat: 1.3, intimidate: 1.5 }
    };

    const emotionModifiers = modifiers[emotion] || {};

    // Apply modifiers to pet's ability effectiveness
    for (const [ability, modifier] of Object.entries(emotionModifiers)) {
      // This would integrate with the combat/utility systems
      // For now, just store the modifier
      if (!this.pet.abilityModifiers) {
        this.pet.abilityModifiers = {};
      }
      this.pet.abilityModifiers[ability] = modifier;
    }
  }

  influenceAIBehavior(emotion, intensity) {
    // This would communicate with the PetAI system
    // to influence decision-making based on current emotion

    if (this.pet.ai) {
      // Adjust AI priorities based on emotion
      switch (emotion) {
        case 'fearful':
          this.pet.ai.behaviorWeights.rest *= 1.5;
          this.pet.ai.behaviorWeights.explore *= 0.3;
          break;
        case 'excited':
          this.pet.ai.behaviorWeights.play *= 1.8;
          this.pet.ai.behaviorWeights.explore *= 1.3;
          break;
        case 'loving':
          this.pet.ai.behaviorWeights.socialize *= 2.0;
          break;
        case 'protective':
          this.pet.ai.behaviorWeights.train *= 1.4;
          break;
      }
    }
  }

  updateEmotionalMemory(emotion, intensity) {
    const memoryKey = `${emotion}_experience`;
    const existingMemory = this.emotionalMemory.get(memoryKey);

    const valence = this.calculateEmotionValence(emotion);
    const newMemory = {
      valence: valence * intensity,
      timestamp: Date.now(),
      context: this.getCurrentEmotionalContext()
    };

    if (existingMemory) {
      // Blend with existing memory
      const blendFactor = 0.3; // 30% new memory, 70% old
      existingMemory.valence = existingMemory.valence * (1 - blendFactor) + newMemory.valence * blendFactor;
      existingMemory.timestamp = newMemory.timestamp;
      existingMemory.context = newMemory.context;
    } else {
      this.emotionalMemory.set(memoryKey, newMemory);
    }
  }

  calculateEmotionValence(emotion) {
    const valences = {
      ecstatic: 1.0,
      happy: 0.8,
      content: 0.6,
      neutral: 0.0,
      excited: 0.7,
      loving: 0.9,
      protective: 0.4,
      unhappy: -0.4,
      sad: -0.7,
      anxious: -0.5,
      angry: -0.6,
      fearful: -0.8
    };

    return valences[emotion] || 0;
  }

  getCurrentEmotionalContext() {
    return {
      location: this.getCurrentEnvironment().type,
      nearbyEntities: this.getNearbyEntities(),
      currentActivity: this.pet.ai?.currentAction?.type || 'none',
      healthStatus: this.pet.currentHealth / this.pet.maxHealth,
      bondingLevel: this.pet.bonding
    };
  }

  getNearbyEntities() {
    // This would check with the world system for nearby entities
    return ['owner']; // Placeholder
  }

  // Public API methods
  getCurrentEmotion() {
    return {
      emotion: this.currentEmotion,
      intensity: this.emotionIntensity,
      moodModifier: this.pet.moodModifier
    };
  }

  getEmotionHistory(duration = 3600000) {
    const cutoffTime = Date.now() - duration;
    return this.emotionHistory.filter(entry => entry.timestamp > cutoffTime);
  }

  forceEmotion(emotion, intensity = 0.8, reason = 'external') {
    this.transitionEmotion(emotion, intensity);
    this.pet.addMemory({
      type: 'forced_emotion',
      content: `Forced to feel ${emotion} (intensity: ${intensity}) - ${reason}`,
      importance: 3
    });
  }

  calmDown() {
    // Gradually reduce emotional intensity
    this.emotionIntensity *= 0.7;
    if (this.emotionIntensity < 0.3) {
      this.currentEmotion = 'content';
      this.emotionIntensity = 0.5;
    }
  }

  soothe() {
    if (['sad', 'angry', 'fearful', 'anxious'].includes(this.currentEmotion)) {
      this.transitionEmotion('content', 0.6);
      this.pet.addMemory({
        type: 'soothed',
        content: 'Was soothed by owner',
        importance: 2
      });
    }
  }

  encourage() {
    if (['unhappy', 'sad', 'anxious'].includes(this.currentEmotion)) {
      this.transitionEmotion('happy', 0.7);
      this.pet.bonding = Math.min(100, this.pet.bonding + 5);
    }
  }
}

module.exports = EmotionalSystem;