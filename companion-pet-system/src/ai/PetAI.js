/**
 * Advanced AI system for pet behavior with personality-driven actions,
 * learning capabilities, and emotional states
 */

class PetAI {
  constructor(pet, world) {
    this.pet = pet;
    this.world = world;
    this.currentAction = null;
    this.actionQueue = [];
    this.lastDecision = Date.now();
    this.decisionInterval = 5000; // Make decisions every 5 seconds

    // AI learning components
    this.behaviorWeights = this.initializeBehaviorWeights();
    this.experienceMemory = new Map();
    this.actionHistory = [];
    this.environmentalMemory = new Map();

    // Emotional system
    this.emotionalState = {
      current: 'neutral',
      intensity: 0.5,
      duration: 0,
      triggers: new Set()
    };

    // Needs-based motivation system
    this.needs = {
      hunger: { current: 50, urgency: 0.5, lastAddressed: Date.now() },
      social: { current: 60, urgency: 0.3, lastAddressed: Date.now() },
      play: { current: 70, urgency: 0.4, lastAddressed: Date.now() },
      rest: { current: 80, urgency: 0.2, lastAddressed: Date.now() },
      exploration: { current: 65, urgency: 0.6, lastAddressed: Date.now() }
    };

    // Personality modifiers
    this.personalityModifiers = this.calculatePersonalityModifiers();
  }

  initializeBehaviorWeights() {
    return {
      socialize: 0.2,
      explore: 0.15,
      play: 0.2,
      rest: 0.15,
      eat: 0.15,
      groom: 0.1,
      train: 0.05
    };
  }

  calculatePersonalityModifiers() {
    const personality = this.pet.personality;
    const modifiers = {};

    // Primary personality influence
    switch (personality.primary) {
      case 'playful':
        modifiers.play = 1.5;
        modifiers.socialize = 1.2;
        break;
      case 'serious':
        modifiers.train = 1.5;
        modifiers.rest = 1.2;
        modifiers.play = 0.7;
        break;
      case 'curious':
        modifiers.explore = 1.8;
        modifiers.train = 1.2;
        break;
      case 'cautious':
        modifiers.rest = 1.3;
        modifiers.explore = 0.7;
        break;
      case 'brave':
        modifiers.explore = 1.3;
        modifiers.train = 1.2;
        break;
      case 'timid':
        modifiers.rest = 1.4;
        modifiers.socialize = 0.6;
        break;
      case 'energetic':
        modifiers.play = 1.4;
        modifiers.explore = 1.3;
        modifiers.rest = 0.6;
        break;
      case 'lazy':
        modifiers.rest = 1.8;
        modifiers.play = 0.5;
        modifiers.explore = 0.4;
        break;
      case 'affectionate':
        modifiers.socialize = 1.6;
        modifiers.play = 1.2;
        break;
      case 'independent':
        modifiers.explore = 1.4;
        modifiers.socialize = 0.7;
        break;
      case 'protective':
        modifiers.train = 1.3;
        modifiers.socialize = 1.1;
        break;
      case 'gentle':
        modifiers.socialize = 1.3;
        modifiers.play = 1.1;
        break;
      case 'mischievous':
        modifiers.play = 1.6;
        modifiers.explore = 1.2;
        break;
      case 'loyal':
        modifiers.socialize = 1.4;
        modifiers.train = 1.2;
        break;
      case 'adventurous':
        modifiers.explore = 1.6;
        modifiers.play = 1.3;
        break;
    }

    // Secondary personality influence
    switch (personality.secondary) {
      case 'playful':
        modifiers.play = (modifiers.play || 1) * 1.2;
        break;
      case 'curious':
        modifiers.explore = (modifiers.explore || 1) * 1.2;
        break;
      case 'affectionate':
        modifiers.socialize = (modifiers.socialize || 1) * 1.2;
        break;
    }

    return modifiers;
  }

  // Main AI update loop
  update() {
    const now = Date.now();

    // Update pet status
    this.pet.updateStatus();
    this.updateNeeds();
    this.updateEmotionalState();

    // Make decisions at intervals
    if (now - this.lastDecision >= this.decisionInterval) {
      this.makeDecision();
      this.lastDecision = now;
    }

    // Process current action
    if (this.currentAction) {
      this.processCurrentAction();
    }

    // Learn from environment
    this.learnFromEnvironment();
  }

  updateNeeds() {
    const now = Date.now();
    const timeSinceLastUpdate = now - this.lastDecision;

    // Update need values based on pet stats
    this.needs.hunger.current = this.pet.hunger;
    this.needs.hunger.urgency = (100 - this.pet.hunger) / 100;

    this.needs.rest.current = this.pet.energy;
    this.needs.rest.urgency = (100 - this.pet.energy) / 100;

    // Calculate social need based on bonding and recent interactions
    const timeSinceLastInteraction = now - (this.pet.lastPlayed || now);
    this.needs.social.current = Math.max(0, 100 - (timeSinceLastInteraction / (1000 * 60 * 60)));
    this.needs.social.urgency = (100 - this.needs.social.current) / 100;

    // Calculate play need based on energy and personality
    const personalityPlayModifier = this.personalityModifiers.play || 1;
    this.needs.play.current = this.pet.energy * personalityPlayModifier;
    this.needs.play.urgency = (100 - this.needs.play.current) / 100;

    // Calculate exploration need based on personality and environment
    const personalityExploreModifier = this.personalityModifiers.explore || 1;
    this.needs.exploration.current = 50 * personalityExploreModifier;
    this.needs.exploration.urgency = personalityExploreModifier * 0.6;
  }

  updateEmotionalState() {
    const prevEmotion = this.emotionalState.current;

    // Determine current emotional state based on needs and mood
    const overallWellbeing = (this.needs.hunger.current + this.needs.rest.current +
                             this.needs.social.current + this.needs.play.current) / 4;

    // Personality influences emotional thresholds
    const emotionalThresholds = this.calculateEmotionalThresholds();

    if (overallWellbeing >= emotionalThresholds.ecstatic) {
      this.emotionalState.current = 'ecstatic';
      this.emotionalState.intensity = Math.min(1.0, (overallWellbeing - 80) / 20);
    } else if (overallWellbeing >= emotionalThresholds.happy) {
      this.emotionalState.current = 'happy';
      this.emotionalState.intensity = (overallWellbeing - 60) / 20;
    } else if (overallWellbeing >= emotionalThresholds.content) {
      this.emotionalState.current = 'content';
      this.emotionalState.intensity = (overallWellbeing - 40) / 20;
    } else if (overallWellbeing >= emotionalThresholds.unhappy) {
      this.emotionalState.current = 'unhappy';
      this.emotionalState.intensity = (40 - overallWellbeing) / 20;
    } else {
      this.emotionalState.current = 'miserable';
      this.emotionalState.intensity = Math.min(1.0, (40 - overallWellbeing) / 40);
    }

    // Check for emotional triggers
    this.checkEmotionalTriggers();

    // If emotion changed, add memory
    if (prevEmotion !== this.emotionalState.current) {
      this.pet.addMemory({
        type: 'emotion_change',
        content: `Felt ${this.emotionalState.current} (intensity: ${this.emotionalState.intensity.toFixed(2)})`,
        importance: 2
      });
    }
  }

  calculateEmotionalThresholds() {
    const personality = this.pet.personality.primary;
    const thresholds = { ecstatic: 85, happy: 70, content: 50, unhappy: 30 };

    // Personality affects emotional stability
    switch (personality) {
      case 'serious':
        thresholds.happy += 5;
        thresholds.content += 5;
        thresholds.unhappy -= 5;
        break;
      case 'playful':
        thresholds.happy -= 5;
        thresholds.ecstatic -= 5;
        break;
      case 'timid':
        thresholds.unhappy += 10;
        thresholds.happy += 5;
        break;
      case 'energetic':
        thresholds.happy -= 5;
        thresholds.ecstatic -= 5;
        break;
      case 'lazy':
        thresholds.content += 10;
        thresholds.unhappy -= 5;
        break;
    }

    return thresholds;
  }

  checkEmotionalTriggers() {
    const triggers = [];

    // Check for extreme states
    if (this.pet.hunger < 20) triggers.push('very_hungry');
    if (this.pet.energy < 20) triggers.push('exhausted');
    if (this.pet.happiness < 20) triggers.push('very_unhappy');
    if (this.pet.cleanliness < 20) triggers.push('very_dirty');

    // Check for positive states
    if (this.pet.hunger > 90) triggers.push('well_fed');
    if (this.pet.energy > 90) triggers.push('well_restored');
    if (this.pet.happiness > 90) triggers.push('very_happy');

    // Check environmental triggers
    const currentWeather = this.world.getCurrentWeather();
    const preferredWeather = this.pet.personality.preferences.preferredWeather;

    if (preferredWeather.includes(currentWeather)) {
      triggers.push('preferred_weather');
    }

    // Update triggers
    this.emotionalState.triggers = new Set(triggers);
  }

  makeDecision() {
    // Calculate action priorities based on needs and personality
    const actionPriorities = this.calculateActionPriorities();

    // Select best action
    const selectedAction = this.selectBestAction(actionPriorities);

    if (selectedAction) {
      this.startAction(selectedAction);
    }
  }

  calculateActionPriorities() {
    const priorities = {};
    const now = Date.now();

    // Base priorities from needs
    for (const [need, data] of Object.entries(this.needs)) {
      if (data.urgency > 0.7) {
        const actionName = this.mapNeedToAction(need);
        if (actionName) {
          priorities[actionName] = data.urgency * 2; // Urgent needs get higher priority
        }
      }
    }

    // Add personality-driven actions
    for (const [behavior, weight] of Object.entries(this.behaviorWeights)) {
      const modifiedWeight = weight * (this.personalityModifiers[behavior] || 1);
      const urgencyModifier = this.getActionUrgencyModifier(behavior);

      priorities[behavior] = (priorities[behavior] || 0) + (modifiedWeight * urgencyModifier);
    }

    // Add learned behavior priorities
    for (const behavior of this.pet.learnedBehaviors) {
      const learnedWeight = this.experienceMemory.get(behavior) || 0.5;
      priorities[behavior] = (priorities[behavior] || 0) + learnedWeight;
    }

    // Add environmental influences
    const environmentalPriorities = this.calculateEnvironmentalPriorities();
    for (const [action, priority] of Object.entries(environmentalPriorities)) {
      priorities[action] = (priorities[action] || 0) + priority;
    }

    // Consider recent actions (avoid repetition)
    const recentActions = this.getRecentActions();
    for (const action of recentActions) {
      priorities[action] = (priorities[action] || 0) * 0.5; // Reduce priority of recent actions
    }

    return priorities;
  }

  mapNeedToAction(need) {
    const needActionMap = {
      hunger: 'eat',
      rest: 'rest',
      social: 'socialize',
      play: 'play',
      exploration: 'explore'
    };
    return needActionMap[need];
  }

  getActionUrgencyModifier(behavior) {
    const now = Date.now();
    const lastAddressed = this.needs[this.mapActionToNeed(behavior)]?.lastAddressed || 0;
    const timeSinceAddressed = now - lastAddressed;
    const hoursSince = timeSinceAddressed / (1000 * 60 * 60);

    // Actions become more urgent over time
    return Math.min(2.0, 1.0 + (hoursSince / 24));
  }

  mapActionToNeed(action) {
    const actionNeedMap = {
      eat: 'hunger',
      rest: 'rest',
      socialize: 'social',
      play: 'play',
      explore: 'exploration'
    };
    return actionNeedMap[action];
  }

  calculateEnvironmentalPriorities() {
    const priorities = {};
    const environment = this.world.getCurrentEnvironment();

    // Weather-based priorities
    const weather = environment.weather;
    if (weather === 'rain' && this.pet.traits.includes('water_affinity')) {
      priorities.play = 0.3;
    }

    if (weather === 'sunny' && this.pet.traits.includes('sun_affinity')) {
      priorities.rest = 0.2;
    }

    // Time of day priorities
    const hour = new Date().getHours();
    if (hour >= 22 || hour <= 6) {
      // Night time - more rest, less exploration
      priorities.rest = (priorities.rest || 0) + 0.3;
      priorities.explore = (priorities.explore || 0) - 0.2;
    } else if (hour >= 10 && hour <= 16) {
      // Day time - more activity
      priorities.play = (priorities.play || 0) + 0.2;
      priorities.explore = (priorities.explore || 0) + 0.2;
    }

    // Location-based priorities
    const location = environment.location;
    if (location.type === 'forest' && this.pet.category === 'animal') {
      priorities.explore = (priorities.explore || 0) + 0.3;
    }

    if (location.type === 'workshop' && this.pet.category === 'construct') {
      priorities.train = (priorities.train || 0) + 0.2;
    }

    return priorities;
  }

  getRecentActions() {
    const now = Date.now();
    const recentTimeframe = 15 * 60 * 1000; // Last 15 minutes

    return this.actionHistory
      .filter(action => now - action.timestamp < recentTimeframe)
      .map(action => action.type);
  }

  selectBestAction(priorities) {
    let bestAction = null;
    let highestPriority = 0;

    for (const [action, priority] of Object.entries(priorities)) {
      if (priority > highestPriority) {
        highestPriority = priority;
        bestAction = action;
      }
    }

    // Random chance for spontaneous behavior (10% chance)
    if (Math.random() < 0.1) {
      const spontaneousActions = ['explore', 'play', 'socialize'];
      const randomAction = spontaneousActions[Math.floor(Math.random() * spontaneousActions.length)];
      if (priorities[randomAction] > 0.1) {
        bestAction = randomAction;
      }
    }

    return bestAction;
  }

  startAction(actionType) {
    const action = {
      type: actionType,
      startTime: Date.now(),
      duration: this.calculateActionDuration(actionType),
      target: this.selectActionTarget(actionType),
      progress: 0,
      successChance: this.calculateActionSuccess(actionType)
    };

    this.currentAction = action;
    this.actionHistory.push({
      type: actionType,
      timestamp: Date.now()
    });

    // Add memory of action start
    this.pet.addMemory({
      type: 'action_start',
      content: `Started ${actionType}`,
      importance: 1
    });
  }

  calculateActionDuration(actionType) {
    const baseDurations = {
      eat: 30000,      // 30 seconds
      rest: 120000,    // 2 minutes
      play: 60000,     // 1 minute
      socialize: 45000, // 45 seconds
      explore: 90000,  // 1.5 minutes
      groom: 40000,    // 40 seconds
      train: 120000    // 2 minutes
    };

    const baseDuration = baseDurations[actionType] || 60000;

    // Personality affects duration
    const personalityModifier = this.getPersonalityDurationModifier(actionType);
    const energyModifier = this.pet.energy / 100; // Low energy = longer rest, shorter play

    return Math.floor(baseDuration * personalityModifier * energyModifier);
  }

  getPersonalityDurationModifier(actionType) {
    const personality = this.pet.personality.primary;

    const modifiers = {
      energetic: { play: 0.7, rest: 1.3, explore: 0.8 },
      lazy: { play: 1.5, rest: 0.7, explore: 1.4 },
      serious: { train: 0.8, play: 1.2, rest: 0.9 },
      playful: { play: 0.6, socialize: 0.8, explore: 0.9 }
    };

    return modifiers[personality]?.[actionType] || 1.0;
  }

  selectActionTarget(actionType) {
    switch (actionType) {
      case 'eat':
        return this.findFoodTarget();
      case 'socialize':
        return this.findSocialTarget();
      case 'play':
        return this.findPlayTarget();
      case 'explore':
        return this.findExplorationTarget();
      case 'groom':
        return this.findGroomingTarget();
      default:
        return null;
    }
  }

  findFoodTarget() {
    // Look for food in owner's inventory or environment
    const ownerInventory = this.world.getOwnerInventory(this.pet.ownerId);
    const availableFood = ownerInventory?.filter(item =>
      item.type === 'food' && this.pet.personality.preferences.favoriteFood === item.id
    );

    if (availableFood && availableFood.length > 0) {
      return { type: 'food', item: availableFood[0] };
    }

    // Look for food in environment
    const environmentalFood = this.world.getEnvironmentalFood();
    if (environmentalFood.length > 0) {
      return { type: 'environmental', item: environmentalFood[0] };
    }

    return null;
  }

  findSocialTarget() {
    // Try to find owner first
    const owner = this.world.getOwner(this.pet.ownerId);
    if (owner && this.world.isInRange(this.pet, owner, 10)) {
      return { type: 'owner', entity: owner };
    }

    // Try to find other pets
    const nearbyPets = this.world.getNearbyPets(this.pet, 20);
    if (nearbyPets.length > 0) {
      return { type: 'pet', entity: nearbyPets[0] };
    }

    return null;
  }

  findPlayTarget() {
    // Check for toys
    const toys = this.world.getNearbyToys(this.pet, 15);
    if (toys.length > 0) {
      return { type: 'toy', item: toys[0] };
    }

    // Default to owner for play
    const owner = this.world.getOwner(this.pet.ownerId);
    if (owner && this.world.isInRange(this.pet, owner, 10)) {
      return { type: 'owner', entity: owner };
    }

    return null;
  }

  findExplorationTarget() {
    // Find interesting locations
    const interestingLocations = this.world.getInterestingLocations(this.pet, 50);
    if (interestingLocations.length > 0) {
      return { type: 'location', target: interestingLocations[0] };
    }

    // Random exploration point
    const randomPoint = this.world.getRandomNearbyPoint(this.pet, 30);
    return { type: 'point', coordinates: randomPoint };
  }

  findGroomingTarget() {
    // Typically self-grooming
    return { type: 'self' };
  }

  calculateActionSuccess(actionType) {
    let baseSuccess = 0.8;

    // Energy affects most actions
    if (actionType !== 'rest') {
      baseSuccess *= (this.pet.energy / 100);
    }

    // Mood affects success
    baseSuccess *= this.pet.moodModifier;

    // Personality affects certain actions
    if (actionType === 'train' && this.pet.personality.primary === 'serious') {
      baseSuccess += 0.1;
    }

    if (actionType === 'play' && this.pet.personality.primary === 'playful') {
      baseSuccess += 0.1;
    }

    return Math.max(0.1, Math.min(1.0, baseSuccess));
  }

  processCurrentAction() {
    if (!this.currentAction) return;

    const now = Date.now();
    const elapsed = now - this.currentAction.startTime;
    const progress = elapsed / this.currentAction.duration;

    this.currentAction.progress = Math.min(1.0, progress);

    // Check if action is complete
    if (this.currentAction.progress >= 1.0) {
      this.completeAction();
    } else {
      // Process ongoing action effects
      this.processOngoingAction();
    }
  }

  processOngoingAction() {
    const action = this.currentAction;

    switch (action.type) {
      case 'rest':
        // Gradually restore energy
        this.pet.energy = Math.min(100, this.pet.energy + 0.5);
        break;
      case 'play':
        // Consume energy gradually
        this.pet.energy = Math.max(0, this.pet.energy - 0.2);
        break;
      case 'explore':
        // Consume energy during exploration
        this.pet.energy = Math.max(0, this.pet.energy - 0.1);
        break;
    }
  }

  completeAction() {
    const action = this.currentAction;
    const success = Math.random() < action.successChance;

    if (success) {
      this.applyActionEffects(action);
      this.learnFromAction(action, true);
    } else {
      this.learnFromAction(action, false);
    }

    // Add completion memory
    this.pet.addMemory({
      type: 'action_complete',
      content: `${success ? 'Successfully' : 'Unsuccessfully'} completed ${action.type}`,
      importance: success ? 1 : 2
    });

    // Update need last addressed time
    const need = this.mapActionToNeed(action.type);
    if (need && this.needs[need]) {
      this.needs[need].lastAddressed = Date.now();
    }

    this.currentAction = null;
  }

  applyActionEffects(action) {
    switch (action.type) {
      case 'eat':
        if (action.target && action.target.item) {
          this.pet.feed(action.target.item);
        }
        break;
      case 'rest':
        this.pet.energy = Math.min(100, this.pet.energy + 30);
        break;
      case 'play':
        this.pet.happiness = Math.min(100, this.pet.happiness + 15);
        this.pet.bonding = Math.min(100, this.pet.bonding + 5);
        break;
      case 'socialize':
        this.pet.happiness = Math.min(100, this.pet.happiness + 10);
        this.pet.bonding = Math.min(100, this.pet.bonding + 8);
        break;
      case 'explore':
        this.pet.gainExperience(5);
        this.pet.happiness = Math.min(100, this.pet.happiness + 8);
        break;
      case 'groom':
        this.pet.cleanliness = Math.min(100, this.pet.cleanliness + 25);
        this.pet.happiness = Math.min(100, this.pet.happiness + 5);
        break;
      case 'train':
        this.pet.gainExperience(15);
        this.pet.skillPoints += 1;
        break;
    }
  }

  learnFromAction(action, success) {
    const learningRate = 0.01;
    const currentWeight = this.experienceMemory.get(action.type) || 0.5;

    // Update behavior weight based on success
    const weightChange = success ? learningRate : -learningRate * 0.5;
    const newWeight = Math.max(0.1, Math.min(1.0, currentWeight + weightChange));

    this.experienceMemory.set(action.type, newWeight);

    // Personality can influence learning
    if (this.pet.personality.primary === 'curious') {
      // Curious pets learn faster
      this.experienceMemory.set(action.type, Math.min(1.0, newWeight + learningRate * 0.5));
    }

    // Check if behavior should be learned permanently
    if (newWeight > 0.8 && !this.pet.learnedBehaviors.has(action.type)) {
      this.pet.learnBehavior(action.type);
    }
  }

  learnFromEnvironment() {
    const environment = this.world.getCurrentEnvironment();
    const memoryKey = `${environment.location.type}_${environment.weather}`;

    // Track environment experiences
    if (!this.environmentalMemory.has(memoryKey)) {
      this.environmentalMemory.set(memoryKey, {
        visits: 0,
        positiveExperiences: 0,
        negativeExperiences: 0
      });
    }

    const envMemory = this.environmentalMemory.get(memoryKey);
    envMemory.visits++;

    // Update based on current emotional state
    if (this.emotionalState.current === 'happy' || this.emotionalState.current === 'ecstatic') {
      envMemory.positiveExperiences++;
    } else if (this.emotionalState.current === 'unhappy' || this.emotionalState.current === 'miserable') {
      envMemory.negativeExperiences++;
    }

    // Learn environmental preferences
    const preferenceScore = envMemory.positiveExperiences / envMemory.visits;
    if (preferenceScore > 0.7 && envMemory.visits > 5) {
      // Pet likes this environment
      if (!this.pet.learnedBehaviors.has(`prefer_${memoryKey}`)) {
        this.pet.learnBehavior(`prefer_${memoryKey}`);
      }
    }
  }

  // EMERGENCY BEHAVIORS
  checkEmergencyBehaviors() {
    // Emergency hunger
    if (this.pet.hunger < 10 && this.currentAction?.type !== 'eat') {
      this.emergencyAction('eat', 'extreme_hunger');
      return true;
    }

    // Emergency exhaustion
    if (this.pet.energy < 5 && this.currentAction?.type !== 'rest') {
      this.emergencyAction('rest', 'exhaustion');
      return true;
    }

    // Emergency unhappiness
    if (this.pet.happiness < 10 && this.pet.bonding > 50) {
      this.emergencyAction('socialize', 'distress');
      return true;
    }

    return false;
  }

  emergencyAction(actionType, reason) {
    // Override current action with emergency action
    this.currentAction = {
      type: actionType,
      startTime: Date.now(),
      duration: this.calculateActionDuration(actionType) * 0.5, // Emergency actions are faster
      target: this.selectActionTarget(actionType),
      progress: 0,
      successChance: 0.9, // High success rate for emergencies
      emergency: true,
      reason: reason
    };

    // Add emergency memory
    this.pet.addMemory({
      type: 'emergency',
      content: `Emergency ${actionType} due to ${reason}`,
      importance: 5
    });
  }

  // SOCIAL INTERACTIONS
  interactWithOtherPet(otherPet) {
    if (!otherPet || !otherPet.ai) return;

    const interaction = this.determineInteractionType(otherPet);
    const success = this.performInteraction(otherPet, interaction);

    // Both pets learn from the interaction
    this.pet.addMemory({
      type: 'pet_interaction',
      content: `Interacted with ${otherPet.name}: ${interaction.type} (${success ? 'success' : 'failure'})`,
      importance: 2
    });

    otherPet.addMemory({
      type: 'pet_interaction',
      content: `Interacted with ${this.pet.name}: ${interaction.type} (${success ? 'success' : 'failure'})`,
      importance: 2
    });

    // Update relationship
    this.updatePetRelationship(otherPet, interaction, success);
  }

  determineInteractionType(otherPet) {
    const myPersonality = this.pet.personality.primary;
    const otherPersonality = otherPet.personality.primary;
    const bondingDifference = Math.abs(this.pet.bonding - otherPet.bonding);

    // Similar personalities bond better
    const personalityMatch = myPersonality === otherPersonality;

    // Determine interaction type
    if (personalityMatch && bondingDifference < 20) {
      return { type: 'friendly', successChance: 0.9 };
    } else if (myPersonality === 'playful' || otherPet.personality.primary === 'playful') {
      return { type: 'play', successChance: 0.8 };
    } else if (myPersonality === 'protective' && this.pet.level > otherPet.level) {
      return { type: 'protective', successChance: 0.85 };
    } else if (myPersonality === 'curious' || otherPet.personality.primary === 'curious') {
      return { type: 'investigative', successChance: 0.7 };
    } else {
      return { type: 'neutral', successChance: 0.6 };
    }
  }

  performInteraction(otherPet, interaction) {
    const success = Math.random() < interaction.successChance;

    if (success) {
      // Positive interaction effects
      this.pet.happiness = Math.min(100, this.pet.happiness + 5);
      otherPet.happiness = Math.min(100, otherPet.happiness + 5);

      // Learn from successful interaction
      const behaviorKey = `interact_${otherPet.typeId}`;
      const currentWeight = this.experienceMemory.get(behaviorKey) || 0.5;
      this.experienceMemory.set(behaviorKey, Math.min(1.0, currentWeight + 0.02));
    } else {
      // Negative interaction effects
      this.pet.happiness = Math.max(0, this.pet.happiness - 2);
      otherPet.happiness = Math.max(0, otherPet.happiness - 2);
    }

    return success;
  }

  updatePetRelationship(otherPet, interaction, success) {
    // This would integrate with a relationship system
    // For now, just affect current mood
    if (success) {
      this.pet.happiness = Math.min(100, this.pet.happiness + 3);
    } else {
      this.pet.happiness = Math.max(0, this.pet.happiness - 1);
    }
  }

  // UTILITY METHODS
  getCurrentAction() {
    return this.currentAction;
  }

  getActionQueue() {
    return [...this.actionQueue];
  }

  getEmotionalState() {
    return { ...this.emotionalState };
  }

  getNeeds() {
    return { ...this.needs };
  }

  forceAction(actionType, target = null) {
    this.currentAction = {
      type: actionType,
      startTime: Date.now(),
      duration: this.calculateActionDuration(actionType),
      target: target || this.selectActionTarget(actionType),
      progress: 0,
      successChance: 1.0,
      forced: true
    };
  }

  pauseAI() {
    this.currentAction = null;
    this.actionQueue = [];
  }

  resumeAI() {
    this.lastDecision = Date.now();
  }
}

module.exports = PetAI;