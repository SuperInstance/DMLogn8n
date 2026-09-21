/**
 * Core Pet class representing individual companion pets
 */

class Pet {
  constructor(petType, owner, customName = null) {
    this.id = this.generatePetId();
    this.typeId = petType.id;
    this.ownerId = owner;
    this.name = customName || petType.name;
    this.level = 1;
    this.experience = 0;
    this.bonding = 0;
    this.happiness = 75;
    this.hunger = 50;
    this.cleanliness = 80;
    this.energy = 100;

    // Inherit base stats from pet type
    this.stats = { ...petType.baseStats };
    this.currentHealth = this.stats.health;
    this.maxHealth = this.stats.health;

    // Evolution stage (0-4)
    this.evolutionStage = 0;
    this.evolutionProgress = 0;

    // AI components
    this.personality = this.generatePersonality(petType);
    this.memories = [];
    this.currentEmotion = 'neutral';
    this.moodModifier = 1.0;
    this.learnedBehaviors = new Set();
    this.autonomousActions = [];

    // Abilities and skills
    this.abilities = [...petType.abilities];
    this.traits = [...petType.traits];
    this.skillPoints = 0;
    this.unlockedSkills = [];

    // Equipment and cosmetics
    this.equipment = {
      collar: null,
      armor: null,
      accessory: null,
      weapon: null
    };
    this.cosmetics = [];

    // Care and maintenance
    this.lastFed = Date.now();
    this.lastGroomed = Date.now();
    this.lastTrained = Date.now();
    this.lastPlayed = Date.now();

    // Metadata
    this.createdAt = Date.now();
    this.lastActive = Date.now();
    this.isActive = false;
    this.isFollowing = false;

    // Breeding and genetics
    this.genetics = {
      fatherId: null,
      motherId: null,
      inheritedTraits: [],
      mutations: []
    };

    // Quest and event associations
    this.associatedQuests = [];
    this.eventFlags = {};
  }

  generatePetId() {
    return 'pet_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
  }

  generatePersonality(petType) {
    const personalityTraits = [
      'playful', 'serious', 'curious', 'cautious', 'brave',
      'timid', 'energetic', 'lazy', 'affectionate', 'independent',
      'protective', 'gentle', 'mischievous', 'loyal', 'adventurous'
    ];

    const personality = {
      primary: this.selectPersonalityTrait(personalityTraits, petType.temperament),
      secondary: this.selectPersonalityTrait(personalityTraits, petType.temperament),
      quirks: this.generateQuirks(2),
      preferences: this.generatePreferences(petType)
    };

    return personality;
  }

  selectPersonalityTrait(traits, temperament) {
    const temperamentTraits = {
      lawful_good: ['loyal', 'protective', 'gentle'],
      neutral_good: ['affectionate', 'curious', 'adventurous'],
      chaotic_good: ['mischievous', 'playful', 'energetic'],
      lawful_neutral: ['serious', 'cautious', 'independent'],
      neutral: ['curious', 'cautious', 'balanced'],
      chaotic_neutral: ['mischievous', 'independent', 'adventurous'],
      lawful_evil: ['protective', 'serious', 'territorial'],
      neutral_evil: ['cautious', 'independent', 'selfish'],
      chaotic_evil: ['mischievous', 'destructive', 'unpredictable']
    };

    const allowedTraits = temperamentTraits[temperament] || traits;
    return allowedTraits[Math.floor(Math.random() * allowedTraits.length)];
  }

  generateQuirks(count) {
    const quirks = [
      'hoarder', 'sleep_eater', 'mood_singer', 'tail_chaser',
      'shadow_pouncer', 'gift_bringer', 'door_guardian', 'weather_sensitive',
      'music_lover', 'color_fascinated', 'night_owl', 'early_bird',
      'food_critique', 'blanket_kicker', 'dream_talker', 'stare_master'
    ];

    const selectedQuirks = [];
    const availableQuirks = [...quirks];

    for (let i = 0; i < count && availableQuirks.length > 0; i++) {
      const index = Math.floor(Math.random() * availableQuirks.length);
      selectedQuirks.push(availableQuirks.splice(index, 1)[0]);
    }

    return selectedQuirks;
  }

  generatePreferences(petType) {
    return {
      favoriteFood: this.selectFavoriteFood(petType.diet),
      favoriteActivity: this.selectFavoriteActivity(),
      preferredWeather: this.selectPreferredWeather(petType.preferredHabitat),
      dislikedElements: this.selectDislikedElements()
    };
  }

  selectFavoriteFood(diet) {
    const foods = {
      carnivore: ['meat', 'fish', 'bone', 'jerky', 'organ_meat'],
      herbivore: ['grass', 'fruits', 'vegetables', 'grains', 'flowers'],
      omnivore: ['mixed_feed', 'berries', 'nuts', 'small_animals', 'plants'],
      none: ['energy_crystal', 'magic_essence', 'void_energy', 'life_force']
    };

    const dietFoods = foods[diet] || foods.omnivore;
    return dietFoods[Math.floor(Math.random() * dietFoods.length)];
  }

  selectFavoriteActivity() {
    const activities = [
      'playing', 'exploring', 'training', 'sleeping', 'eating',
      'grooming', 'socializing', 'hunting', 'guarding', 'cuddling'
    ];
    return activities[Math.floor(Math.random() * activities.length)];
  }

  selectPreferredWeather(habitat) {
    const weatherPreferences = {
      forest: ['sunny', 'cloudy', 'light_rain'],
      mountain: ['clear', 'windy', 'snow'],
      desert: ['sunny', 'hot', 'dry'],
      arctic: ['snow', 'cold', 'blizzard'],
      volcanic: ['hot', 'ash', 'lava_glow'],
      urban: ['mild', 'cloudy', 'light_rain'],
      enchanted_forest: ['magical', 'aurora', 'sparkling'],
      dark_forest: ['foggy', 'moonlight', 'shadowy']
    };

    const preferences = weatherPreferences[habitat] || weatherPreferences.forest;
    return preferences[Math.floor(Math.random() * preferences.length)];
  }

  selectDislikedElements() {
    const elements = ['fire', 'water', 'thunder', 'darkness', 'bright_light', 'cold', 'heat'];
    const count = Math.floor(Math.random() * 2) + 1; // 1-2 disliked elements
    const disliked = [];

    for (let i = 0; i < count; i++) {
      const index = Math.floor(Math.random() * elements.length);
      disliked.push(elements.splice(index, 1)[0]);
    }

    return disliked;
  }

  // Status updates
  updateStatus() {
    const now = Date.now();
    const hoursSinceLastFed = (now - this.lastFed) / (1000 * 60 * 60);
    const hoursSinceLastGroomed = (now - this.lastGroomed) / (1000 * 60 * 60);

    // Natural stat decay
    this.hunger = Math.max(0, this.hunger - hoursSinceLastFed * 2);
    this.happiness = Math.max(0, this.happiness - hoursSinceLastFed * 1);
    this.cleanliness = Math.max(0, this.cleanliness - hoursSinceLastGroomed * 1.5);

    // Energy regeneration
    this.energy = Math.min(100, this.energy + 0.1);

    // Health regeneration if well cared for
    if (this.hunger > 70 && this.happiness > 70 && this.cleanliness > 70) {
      this.currentHealth = Math.min(this.maxHealth, this.currentHealth + 0.5);
    }

    // Update mood based on status
    this.updateMood();

    this.lastActive = now;
  }

  updateMood() {
    const overallWellbeing = (this.happiness + this.hunger + this.cleanliness + this.energy) / 4;

    if (overallWellbeing >= 90) {
      this.currentEmotion = 'ecstatic';
      this.moodModifier = 1.3;
    } else if (overallWellbeing >= 75) {
      this.currentEmotion = 'happy';
      this.moodModifier = 1.15;
    } else if (overallWellbeing >= 60) {
      this.currentEmotion = 'content';
      this.moodModifier = 1.0;
    } else if (overallWellbeing >= 40) {
      this.currentEmotion = 'unhappy';
      this.moodModifier = 0.85;
    } else if (overallWellbeing >= 20) {
      this.currentEmotion = 'sad';
      this.moodModifier = 0.7;
    } else {
      this.currentEmotion = 'miserable';
      this.moodModifier = 0.5;
    }
  }

  // Experience and leveling
  gainExperience(amount) {
    this.experience += amount;
    const expNeeded = this.calculateExperienceNeeded();

    if (this.experience >= expNeeded) {
      this.levelUp();
    }
  }

  calculateExperienceNeeded() {
    return Math.floor(100 * Math.pow(1.5, this.level - 1));
  }

  levelUp() {
    this.level++;
    this.experience = 0;

    // Increase stats
    const statIncrease = Math.floor(Math.random() * 3) + 2;
    const stats = ['health', 'attack', 'defense', 'speed', 'intelligence'];
    const statToIncrease = stats[Math.floor(Math.random() * stats.length)];

    this.stats[statToIncrease] += statIncrease;
    if (statToIncrease === 'health') {
      this.maxHealth += statIncrease;
      this.currentHealth = this.maxHealth;
    }

    // Gain skill point
    this.skillPoints++;

    // Increase bonding
    this.bonding = Math.min(100, this.bonding + 5);

    return {
      level: this.level,
      statIncreased: statToIncrease,
      amount: statIncrease,
      skillPoints: this.skillPoints
    };
  }

  // Bonding and relationship
  increaseBonding(amount) {
    this.bonding = Math.min(100, this.bonding + amount);
    this.happiness = Math.min(100, this.happiness + amount / 2);
  }

  decreaseBonding(amount) {
    this.bonding = Math.max(0, this.bonding - amount);
    this.happiness = Math.max(0, this.happiness - amount / 2);
  }

  // Care actions
  feed(food) {
    const hungerIncrease = this.calculateFoodEffectiveness(food);
    this.hunger = Math.min(100, this.hunger + hungerIncrease);
    this.happiness = Math.min(100, this.happiness + 5);
    this.lastFed = Date.now();

    // Favorite food bonus
    if (food === this.personality.preferences.favoriteFood) {
      this.happiness = Math.min(100, this.happiness + 15);
      this.bonding = Math.min(100, this.bonding + 3);
    }

    return {
      hungerRestored: hungerIncrease,
      happinessIncrease: 5,
      bondingIncrease: 1
    };
  }

  calculateFoodEffectiveness(food) {
    const baseEffectiveness = 20;
    const isFavorite = food === this.personality.preferences.favoriteFood;
    const qualityBonus = Math.floor(Math.random() * 10) + 5;

    return baseEffectiveness + (isFavorite ? 15 : 0) + qualityBonus;
  }

  groom() {
    this.cleanliness = Math.min(100, this.cleanliness + 30);
    this.happiness = Math.min(100, this.happiness + 10);
    this.bonding = Math.min(100, this.bonding + 2);
    this.lastGroomed = Date.now();

    return {
      cleanlinessIncrease: 30,
      happinessIncrease: 10,
      bondingIncrease: 2
    };
  }

  play(activity) {
    const energyCost = 20;
    if (this.energy < energyCost) {
      return { success: false, reason: 'too_tired' };
    }

    this.energy -= energyCost;
    this.happiness = Math.min(100, this.happiness + 15);
    this.bonding = Math.min(100, this.bonding + 3);

    // Favorite activity bonus
    if (activity === this.personality.preferences.favoriteActivity) {
      this.happiness = Math.min(100, this.happiness + 10);
      this.gainExperience(10);
    }

    this.lastPlayed = Date.now();

    return {
      success: true,
      energyCost: energyCost,
      happinessIncrease: 15,
      bondingIncrease: 3
    };
  }

  // Memory and learning
  addMemory(memory) {
    this.memories.push({
      timestamp: Date.now(),
      type: memory.type,
      content: memory.content,
      emotion: this.currentEmotion,
      importance: memory.importance || 1
    });

    // Limit memory size
    if (this.memories.length > 100) {
      this.memories.shift();
    }
  }

  learnBehavior(behavior) {
    this.learnedBehaviors.add(behavior);
    this.addMemory({
      type: 'learning',
      content: `Learned behavior: ${behavior}`,
      importance: 2
    });
  }

  // Equipment management
  equipItem(item, slot) {
    if (this.equipment[slot]) {
      // Unequip current item
      this.unequipItem(slot);
    }

    this.equipment[slot] = item;
    this.applyItemEffects(item, 'equip');
  }

  unequipItem(slot) {
    const item = this.equipment[slot];
    if (item) {
      this.applyItemEffects(item, 'unequip');
      this.equipment[slot] = null;
    }
  }

  applyItemEffects(item, action) {
    const multiplier = action === 'equip' ? 1 : -1;

    if (item.stats) {
      for (const [stat, value] of Object.entries(item.stats)) {
        this.stats[stat] += value * multiplier;
      }
    }

    if (item.abilities) {
      if (action === 'equip') {
        this.abilities.push(...item.abilities);
      } else {
        this.abilities = this.abilities.filter(ability =>
          !item.abilities.includes(ability)
        );
      }
    }
  }

  // Serialization
  toJSON() {
    return {
      id: this.id,
      typeId: this.typeId,
      ownerId: this.ownerId,
      name: this.name,
      level: this.level,
      experience: this.experience,
      bonding: this.bonding,
      happiness: this.happiness,
      hunger: this.hunger,
      cleanliness: this.cleanliness,
      energy: this.energy,
      stats: this.stats,
      currentHealth: this.currentHealth,
      maxHealth: this.maxHealth,
      evolutionStage: this.evolutionStage,
      evolutionProgress: this.evolutionProgress,
      personality: this.personality,
      memories: this.memories.slice(-50), // Only last 50 memories
      currentEmotion: this.currentEmotion,
      moodModifier: this.moodModifier,
      learnedBehaviors: Array.from(this.learnedBehaviors),
      abilities: this.abilities,
      traits: this.traits,
      skillPoints: this.skillPoints,
      unlockedSkills: this.unlockedSkills,
      equipment: this.equipment,
      cosmetics: this.cosmetics,
      lastFed: this.lastFed,
      lastGroomed: this.lastGroomed,
      lastTrained: this.lastTrained,
      lastPlayed: this.lastPlayed,
      createdAt: this.createdAt,
      lastActive: this.lastActive,
      isActive: this.isActive,
      isFollowing: this.isFollowing,
      genetics: this.genetics,
      associatedQuests: this.associatedQuests,
      eventFlags: this.eventFlags
    };
  }

  static fromJSON(data) {
    const pet = Object.create(Pet.prototype);
    Object.assign(pet, data);
    pet.learnedBehaviors = new Set(data.learnedBehaviors);
    return pet;
  }
}

module.exports = Pet;