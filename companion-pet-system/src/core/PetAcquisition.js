/**
 * Pet acquisition system with multiple methods:
 * - Taming wild creatures
 * - Summoning magical entities
 * - Breeding existing pets
 * - Quest rewards
 * - Special events and seasonal pets
 */

class PetAcquisition {
  constructor(petDatabase, playerManager) {
    this.petDatabase = petDatabase;
    this.playerManager = playerManager;
    this.activeTamingSessions = new Map();
    this.breedingRequests = new Map();
    this.summoningRituals = new Map();
  }

  // TAMING SYSTEM
  async attemptTaming(playerId, creatureId, tamingMethod = 'standard') {
    const player = await this.playerManager.getPlayer(playerId);
    const creature = await this.getCreature(creatureId);

    if (!player || !creature) {
      return { success: false, reason: 'invalid_player_or_creature' };
    }

    const tamingData = {
      playerId,
      creatureId,
      method: tamingMethod,
      startTime: Date.now(),
      progress: 0,
      successChance: this.calculateTamingSuccess(player, creature, tamingMethod),
      requirements: this.getTamingRequirements(creature, tamingMethod)
    };

    // Check if player meets requirements
    const requirementsMet = await this.checkTamingRequirements(player, tamingData.requirements);
    if (!requirementsMet.success) {
      return requirementsMet;
    }

    // Start taming session
    this.activeTamingSessions.set(`${playerId}_${creatureId}`, tamingData);

    return {
      success: true,
      sessionId: `${playerId}_${creatureId}`,
      estimatedTime: this.calculateTamingTime(creature, tamingMethod),
      successChance: tamingData.successChance
    };
  }

  calculateTamingSuccess(player, creature, method) {
    let baseChance = 0.3; // 30% base success rate

    // Player skill modifiers
    const tamingSkill = player.skills?.taming || 0;
    baseChance += tamingSkill * 0.05; // 5% per skill level

    // Creature difficulty modifier
    const difficultyModifiers = {
      common: 0.2,
      uncommon: 0.1,
      rare: 0.0,
      epic: -0.1,
      legendary: -0.2
    };
    baseChance += difficultyModifiers[creature.rarity] || 0;

    // Method modifiers
    const methodModifiers = {
      standard: 0,
      food_bait: 0.15,
      magical_aid: 0.2,
      ritual: 0.25,
      master_tamer: 0.3
    };
    baseChance += methodModifiers[method] || 0;

    // Equipment bonuses
    if (player.equipment?.taming_tools) {
      baseChance += player.equipment.taming_tools.bonus || 0;
    }

    // Environmental factors
    const environmentBonus = this.getEnvironmentBonus(player.currentLocation, creature.preferredHabitat);
    baseChance += environmentBonus;

    return Math.max(0.05, Math.min(0.95, baseChance)); // Clamp between 5% and 95%
  }

  getTamingRequirements(creature, method) {
    const baseRequirements = {
      level: Math.max(1, creature.baseStats.level - 5),
      skill_taming: method === 'master_tamer' ? 10 : method === 'ritual' ? 5 : 1
    };

    const methodRequirements = {
      food_bait: { items: [{ id: 'taming_bait', quantity: 3 }] },
      magical_aid: { items: [{ id: 'mana_crystal', quantity: 2 }], spells: ['charm_animal'] },
      ritual: { items: [{ id: 'binding_rune', quantity: 1 }, { id: 'offering', quantity: 1 }],
                skills: ['ritual_magic'] },
      master_tamer: { achievements: ['master_tamer'], skills: ['advanced_taming'] }
    };

    return {
      ...baseRequirements,
      ...(methodRequirements[method] || {})
    };
  }

  async checkTamingRequirements(player, requirements) {
    // Check level requirement
    if (player.level < requirements.level) {
      return { success: false, reason: 'insufficient_level', required: requirements.level };
    }

    // Check skill requirements
    if (requirements.skill_taming && (player.skills?.taming || 0) < requirements.skill_taming) {
      return { success: false, reason: 'insufficient_skill', required: requirements.skill_taming };
    }

    // Check item requirements
    if (requirements.items) {
      for (const item of requirements.items) {
        const playerItem = player.inventory?.find(i => i.id === item.id);
        if (!playerItem || playerItem.quantity < item.quantity) {
          return { success: false, reason: 'missing_item', item: item.id, required: item.quantity };
        }
      }
    }

    // Check spell requirements
    if (requirements.spells) {
      for (const spell of requirements.spells) {
        if (!player.spells?.includes(spell)) {
          return { success: false, reason: 'missing_spell', spell: spell };
        }
      }
    }

    // Check skill requirements
    if (requirements.skills) {
      for (const skill of requirements.skills) {
        if (!player.skills?.[skill]) {
          return { success: false, reason: 'missing_skill', skill: skill };
        }
      }
    }

    return { success: true };
  }

  async completeTaming(sessionId) {
    const session = this.activeTamingSessions.get(sessionId);
    if (!session) {
      return { success: false, reason: 'session_not_found' };
    }

    // Calculate final success
    const randomRoll = Math.random();
    const success = randomRoll <= session.successChance;

    if (success) {
      // Create pet
      const petType = this.petDatabase.getPetType(session.creatureId);
      const player = await this.playerManager.getPlayer(session.playerId);

      const Pet = require('./Pet');
      const newPet = new Pet(petType, session.playerId);

      // Add taming-specific traits
      newPet.traits.push('tamed');
      if (session.method === 'master_tamer') {
        newPet.traits.push('expertly_tamed');
      }

      // Add memory of taming
      newPet.addMemory({
        type: 'taming',
        content: `Was tamed by ${player.name}`,
        importance: 5
      });

      // Add pet to player
      await this.playerManager.addPet(session.playerId, newPet);

      // Clean up session
      this.activeTamingSessions.delete(sessionId);

      return {
        success: true,
        pet: newPet,
        tamingMethod: session.method,
        bondingBonus: this.calculateTamingBondingBonus(session.method)
      };
    } else {
      // Taming failed
      this.activeTamingSessions.delete(sessionId);
      return {
        success: false,
        reason: 'taming_failed',
        difficulty: 'The creature resisted taming attempts'
      };
    }
  }

  // SUMMONING SYSTEM
  async attemptSummoning(playerId, summoningType, offerings = []) {
    const player = await this.playerManager.getPlayer(playerId);
    if (!player) {
      return { success: false, reason: 'invalid_player' };
    }

    const summoningRitual = this.getSummoningRitual(summoningType);
    if (!summoningRitual) {
      return { success: false, reason: 'invalid_summoning_type' };
    }

    // Validate offerings
    const offeringValidation = this.validateOfferings(offerings, summoningRitual.requirements);
    if (!offeringValidation.valid) {
      return { success: false, reason: 'invalid_offerings', details: offeringValidation };
    }

    // Calculate success chance
    const successChance = this.calculateSummoningSuccess(player, summoningRitual, offerings);

    // Create summoning session
    const sessionId = `${playerId}_${summoningType}_${Date.now()}`;
    this.summoningRituals.set(sessionId, {
      playerId,
      type: summoningType,
      ritual: summoningRitual,
      offerings,
      successChance,
      startTime: Date.now(),
      duration: summoningRitual.duration
    });

    // Consume offerings
    await this.consumeOfferings(playerId, offerings);

    return {
      success: true,
      sessionId,
      successChance,
      duration: summoningRitual.duration,
      possiblePets: summoningRitual.possiblePets
    };
  }

  getSummoningRitual(type) {
    const rituals = {
      basic_familiar: {
        name: 'Basic Familiar Summoning',
        requirements: { mana_crystal: 1, essence_of_magic: 1 },
        duration: 300000, // 5 minutes
        successModifier: 0,
        possiblePets: ['fairy_dragon', 'owl', 'cat', 'clockwork_familiar']
      },
      elemental_binding: {
        name: 'Elemental Binding Ritual',
        requirements: { elemental_core: 1, binding_rune: 2, mana_crystal: 3 },
        duration: 600000, // 10 minutes
        successModifier: -0.1,
        possiblePets: ['fire_elemental', 'ice_elemental', 'earth_elemental', 'air_elemental']
      },
      dark_pact: {
        name: 'Dark Pact Ritual',
        requirements: { dark_crystal: 1, blood_essence: 2, shadow_essence: 1 },
        duration: 900000, // 15 minutes
        successModifier: -0.2,
        possiblePets: ['shadow_wolf', 'skeletal_hound', 'void_stalker', 'demon_imp']
      },
      celestial_summoning: {
        name: 'Celestial Summoning',
        requirements: { celestial_crystal: 1, holy_water: 3, blessing_scroll: 1 },
        duration: 1200000, // 20 minutes
        successModifier: -0.15,
        possiblePets: ['celestial_guardian', 'angelic_familiar', 'light_elemental', 'phoenix']
      },
      dragon_egg_hatching: {
        name: 'Dragon Egg Hatching',
        requirements: { dragon_egg: 1, fire_essence: 2, incubator: 1 },
        duration: 86400000, // 24 hours
        successModifier: 0.1,
        possiblePets: ['dragon_whelp', 'baby_dragon']
      }
    };

    return rituals[type];
  }

  validateOfferings(offerings, requirements) {
    const missing = [];
    const extra = [];

    // Check for missing required items
    for (const [itemId, quantity] of Object.entries(requirements)) {
      const offered = offerings.find(o => o.id === itemId);
      if (!offered || offered.quantity < quantity) {
        missing.push({ id: itemId, required: quantity, offered: offered?.quantity || 0 });
      }
    }

    // Check for extra items (not necessarily bad, but good to know)
    for (const offering of offerings) {
      if (!requirements[offering.id]) {
        extra.push(offering.id);
      }
    }

    return {
      valid: missing.length === 0,
      missing,
      extra
    };
  }

  calculateSummoningSuccess(player, ritual, offerings) {
    let baseChance = 0.5; // 50% base success

    // Player magical affinity
    const magicSkill = player.skills?.magic || 0;
    baseChance += magicSkill * 0.03;

    // Ritual difficulty
    baseChance += ritual.successModifier;

    // Offering quality bonuses
    for (const offering of offerings) {
      if (offering.quality === 'rare') baseChance += 0.05;
      if (offering.quality === 'epic') baseChance += 0.1;
      if (offering.quality === 'legendary') baseChance += 0.15;
    }

    // Location bonuses
    const locationBonus = this.getLocationSummoningBonus(player.currentLocation, ritual.type);
    baseChance += locationBonus;

    return Math.max(0.1, Math.min(0.9, baseChance));
  }

  async completeSummoning(sessionId) {
    const session = this.summoningRituals.get(sessionId);
    if (!session) {
      return { success: false, reason: 'session_not_found' };
    }

    const success = Math.random() <= session.successChance;

    if (success) {
      // Select random pet from possible pets
      const possiblePetIds = session.ritual.possiblePets;
      const selectedPetId = possiblePetIds[Math.floor(Math.random() * possiblePetIds.length)];
      const petType = this.petDatabase.getPetType(selectedPetId);

      const Pet = require('./Pet');
      const newPet = new Pet(petType, session.playerId);

      // Add summoning-specific traits
      newPet.traits.push('summoned');
      newPet.traits.push(`${session.type}_summoned`);

      // Add memory of summoning
      newPet.addMemory({
        type: 'summoning',
        content: `Was summoned through ${session.ritual.name}`,
        importance: 4
      });

      // Add pet to player
      await this.playerManager.addPet(session.playerId, newPet);

      this.summoningRituals.delete(sessionId);

      return {
        success: true,
        pet: newPet,
        summoningType: session.type,
        ritualUsed: session.ritual.name
      };
    } else {
      this.summoningRituals.delete(sessionId);
      return {
        success: false,
        reason: 'summoning_failed',
        message: 'The summoning ritual failed to bind a creature'
      };
    }
  }

  // BREEDING SYSTEM
  async requestBreeding(playerId, pet1Id, pet2Id) {
    const player = await this.playerManager.getPlayer(playerId);
    const pet1 = await this.playerManager.getPet(playerId, pet1Id);
    const pet2 = await this.playerManager.getPet(playerId, pet2Id);

    if (!player || !pet1 || !pet2) {
      return { success: false, reason: 'invalid_entities' };
    }

    // Validate breeding compatibility
    const compatibility = this.checkBreedingCompatibility(pet1, pet2);
    if (!compatibility.canBreed) {
      return { success: false, reason: compatibility.reason };
    }

    // Check breeding cooldown
    const cooldownCheck = this.checkBreedingCooldown(pet1, pet2);
    if (!cooldownCheck.canBreed) {
      return { success: false, reason: 'breeding_cooldown', timeRemaining: cooldownCheck.timeRemaining };
    }

    // Calculate breeding cost
    const breedingCost = this.calculateBreedingCost(pet1, pet2);

    // Create breeding request
    const requestId = `${playerId}_${pet1Id}_${pet2Id}_${Date.now()}`;
    this.breedingRequests.set(requestId, {
      playerId,
      pet1Id,
      pet2Id,
      cost: breedingCost,
      startTime: Date.now(),
      duration: this.calculateBreedingTime(pet1, pet2),
      expectedTraits: this.predictOffspringTraits(pet1, pet2)
    });

    return {
      success: true,
      requestId,
      duration: this.calculateBreedingTime(pet1, pet2),
      cost: breedingCost,
      expectedTraits: this.predictOffspringTraits(pet1, pet2)
    };
  }

  checkBreedingCompatibility(pet1, pet2) {
    // Can't breed with self
    if (pet1.id === pet2.id) {
      return { canBreed: false, reason: 'same_pet' };
    }

    // Both pets must be at evolution stage 2 or higher
    if (pet1.evolutionStage < 2 || pet2.evolutionStage < 2) {
      return { canBreed: false, reason: 'insufficient_evolution' };
    }

    // Check species compatibility
    const compatible = this.areSpeciesCompatible(pet1.typeId, pet2.typeId);
    if (!compatible) {
      return { canBreed: false, reason: 'incompatible_species' };
    }

    // Check relationship compatibility
    if (pet1.currentEmotion === 'miserable' || pet2.currentEmotion === 'miserable') {
      return { canBreed: false, reason: 'unhappy_pets' };
    }

    return { canBreed: true };
  }

  areSpeciesCompatible(species1, species2) {
    // Same species are always compatible
    if (species1 === species2) return true;

    // Define compatibility groups
    const compatibilityGroups = {
      canines: ['wolf', 'shadow_wolf', 'skeletal_hound'],
      felines: ['cat', 'lion', 'tiger'],
      avians: ['owl', 'phoenix', 'griffin'],
      dragons: ['dragon_whelp', 'ancient_dragon', 'fairy_dragon'],
      elementals: ['fire_elemental', 'ice_elemental', 'earth_elemental', 'air_elemental'],
      undead: ['skeletal_hound', 'zombie', 'ghost'],
      constructs: ['golem_companion', 'clockwork_familiar']
    };

    // Check if both species belong to the same compatibility group
    for (const group of Object.values(compatibilityGroups)) {
      if (group.includes(species1) && group.includes(species2)) {
        return true;
      }
    }

    // Special cross-species breeding (rare)
    const specialCrosses = [
      ['wolf', 'fairy_dragon'], // Wolf-dragon hybrids
      ['phoenix', 'ice_elemental'], // Phoenix-elemental hybrids
      ['unicorn', 'fairy_dragon'] // Magical creature hybrids
    ];

    for (const [speciesA, speciesB] of specialCrosses) {
      if ((species1 === speciesA && species2 === speciesB) ||
          (species1 === speciesB && species2 === speciesA)) {
        return true;
      }
    }

    return false;
  }

  checkBreedingCooldown(pet1, pet2) {
    const now = Date.now();
    const cooldownPeriod = 24 * 60 * 60 * 1000; // 24 hours

    const lastBred1 = pet1.lastBred || 0;
    const lastBred2 = pet2.lastBred || 0;

    const timeSinceLastBred1 = now - lastBred1;
    const timeSinceLastBred2 = now - lastBred2;

    if (timeSinceLastBred1 < cooldownPeriod || timeSinceLastBred2 < cooldownPeriod) {
      const timeRemaining = Math.max(
        cooldownPeriod - timeSinceLastBred1,
        cooldownPeriod - timeSinceLastBred2
      );
      return { canBreed: false, timeRemaining };
    }

    return { canBreed: true };
  }

  calculateBreedingCost(pet1, pet2) {
    const baseCost = 100;
    const rarityMultiplier = (this.getRarityValue(pet1.rarity) + this.getRarityValue(pet2.rarity)) / 2;
    const levelMultiplier = (pet1.level + pet2.level) / 20;

    return Math.floor(baseCost * rarityMultiplier * levelMultiplier);
  }

  getRarityValue(rarity) {
    const values = {
      common: 1,
      uncommon: 1.5,
      rare: 2,
      epic: 3,
      legendary: 5
    };
    return values[rarity] || 1;
  }

  calculateBreedingTime(pet1, pet2) {
    const baseTime = 3600000; // 1 hour
    const rarityBonus = (this.getRarityValue(pet1.rarity) + this.getRarityValue(pet2.rarity)) * 1800000;
    const bondingBonus = ((pet1.bonding + pet2.bonding) / 200) * -0.3; // Better bonding reduces time

    return Math.floor(baseTime + rarityBonus) * (1 + bondingBonus);
  }

  predictOffspringTraits(pet1, pet2) {
    const offspringTraits = {
      possibleSpecies: [pet1.typeId, pet2.typeId],
      inheritedTraits: [],
      possibleRarities: [pet1.rarity, pet2.rarity],
      mutationChance: 0.1 // 10% chance of mutation
    };

    // Combine parent traits
    const allTraits = [...new Set([...pet1.traits, ...pet2.traits])];
    offspringTraits.inheritedTraits = allTraits.slice(0, 8); // Limit to 8 traits

    // Rarity inheritance chance
    if (pet1.rarity === pet2.rarity && pet1.rarity !== 'common') {
      offspringTraits.possibleRarities.push(this.upgradeRarity(pet1.rarity));
    }

    return offspringTraits;
  }

  upgradeRarity(currentRarity) {
    const rarityUpgrade = {
      common: 'uncommon',
      uncommon: 'rare',
      rare: 'epic',
      epic: 'legendary',
      legendary: 'legendary'
    };
    return rarityUpgrade[currentRarity] || currentRarity;
  }

  async completeBreeding(requestId) {
    const request = this.breedingRequests.get(requestId);
    if (!request) {
      return { success: false, reason: 'request_not_found' };
    }

    const player = await this.playerManager.getPlayer(request.playerId);
    const pet1 = await this.playerManager.getPet(request.playerId, request.pet1Id);
    const pet2 = await this.playerManager.getPet(request.playerId, request.pet2Id);

    // Determine offspring characteristics
    const offspringData = this.generateOffspring(pet1, pet2, request.expectedTraits);
    const petType = this.petDatabase.getPetType(offspringData.species);

    const Pet = require('./Pet');
    const offspring = new Pet(petType, request.playerId);

    // Apply genetics
    offspring.genetics = {
      fatherId: pet1.id,
      motherId: pet2.id,
      inheritedTraits: offspringData.inheritedTraits,
      mutations: offspringData.mutations
    };

    // Apply inherited traits
    offspring.traits.push(...offspringData.inheritedTraits);
    if (offspringData.mutations.length > 0) {
      offspring.traits.push(...offspringData.mutations);
      offspring.traits.push('mutated');
    }

    // Add breeding memory
    offspring.addMemory({
      type: 'birth',
      content: `Born from breeding of ${pet1.name} and ${pet2.name}`,
      importance: 5
    });

    // Add to player's pets
    await this.playerManager.addPet(request.playerId, offspring);

    // Update parents' breeding cooldown
    pet1.lastBred = Date.now();
    pet2.lastBred = Date.now();

    // Clean up request
    this.breedingRequests.delete(requestId);

    return {
      success: true,
      offspring: offspring,
      parents: {
        father: { id: pet1.id, name: pet1.name },
        mother: { id: pet2.id, name: pet2.name }
      },
      mutations: offspringData.mutations
    };
  }

  generateOffspring(pet1, pet2, expectedTraits) {
    const species = Math.random() < 0.5 ? pet1.typeId : pet2.typeId;
    const inheritedTraits = this.selectInheritedTraits(pet1.traits, pet2.traits);
    const mutations = Math.random() < 0.1 ? this.generateMutations(species) : [];

    return {
      species,
      inheritedTraits,
      mutations,
      rarity: this.determineOffspringRarity(pet1.rarity, pet2.rarity, mutations.length)
    };
  }

  selectInheritedTraits(traits1, traits2) {
    const allTraits = [...new Set([...traits1, ...traits2])];
    const inherited = [];

    // Select 3-5 random traits from parents
    const numTraits = Math.floor(Math.random() * 3) + 3;
    const availableTraits = [...allTraits];

    for (let i = 0; i < numTraits && availableTraits.length > 0; i++) {
      const index = Math.floor(Math.random() * availableTraits.length);
      inherited.push(availableTraits.splice(index, 1)[0]);
    }

    return inherited;
  }

  generateMutations(species) {
    const possibleMutations = {
      wolf: ['enhanced_senses', 'alpha_presence', 'shadow_coat'],
      cat: ['nine_lives', 'perfect_balance', 'night_vision_plus'],
      dragon: ['elemental_breath', 'ancient_wisdom', 'wings_of_power'],
      phoenix: ['eternal_flame', 'rebirth_master', 'solar_wings'],
      unicorn: ['purification_aura', 'healing_touch', 'rainbow_horn']
    };

    const speciesMutations = possibleMutations[species] || ['enhanced_stat', 'special_ability', 'unique_appearance'];
    const numMutations = Math.random() < 0.05 ? 2 : 1; // 5% chance for 2 mutations

    const mutations = [];
    const available = [...speciesMutations];

    for (let i = 0; i < numMutations && available.length > 0; i++) {
      const index = Math.floor(Math.random() * available.length);
      mutations.push(available.splice(index, 1)[0]);
    }

    return mutations;
  }

  determineOffspringRarity(rarity1, rarity2, mutationCount) {
    const rarityValues = {
      common: 1,
      uncommon: 2,
      rare: 3,
      epic: 4,
      legendary: 5
    };

    const averageRarity = (rarityValues[rarity1] + rarityValues[rarity2]) / 2;
    let offspringRarity = rarity1;

    // Mutations can increase rarity
    if (mutationCount > 0) {
      averageRarity += mutationCount;
    }

    // Determine rarity based on average
    if (averageRarity >= 4.5) offspringRarity = 'legendary';
    else if (averageRarity >= 3.5) offspringRarity = 'epic';
    else if (averageRarity >= 2.5) offspringRarity = 'rare';
    else if (averageRarity >= 1.5) offspringRarity = 'uncommon';
    else offspringRarity = 'common';

    return offspringRarity;
  }

  // QUEST AND EVENT REWARDS
  async generateQuestRewardPet(playerId, questLevel, questTheme) {
    const possiblePets = this.getQuestRewardPets(questLevel, questTheme);
    const selectedPetType = possiblePets[Math.floor(Math.random() * possiblePets.length)];

    const Pet = require('./Pet');
    const questPet = new Pet(selectedPetType, playerId);

    // Quest-specific traits
    questPet.traits.push('quest_reward');
    questPet.traits.push(`${questTheme}_companion`);

    // Enhanced starting stats for quest rewards
    for (const stat in questPet.stats) {
      questPet.stats[stat] = Math.floor(questPet.stats[stat] * 1.2);
    }

    // Add quest memory
    questPet.addMemory({
      type: 'quest_reward',
      content: `Received as a reward for completing a ${questTheme} quest`,
      importance: 3
    });

    return questPet;
  }

  getQuestRewardPets(questLevel, questTheme) {
    const themePets = {
      forest: ['wolf', 'owl', 'fairy_dragon', 'unicorn'],
      mountain: ['griffin', 'dragon_whelp', 'eagle'],
      dungeon: ['skeletal_hound', 'shadow_wolf', 'goblin_companion'],
      magical: ['fairy_dragon', 'phoenix', 'elemental', 'unicorn'],
      urban: ['cat', 'dog', 'clockwork_familiar'],
      seasonal: this.getSeasonalPets()
    };

    const availablePets = themePets[questTheme] || themePets.forest;

    // Filter by level appropriateness
    return availablePets.filter(petId => {
      const petType = this.petDatabase.getPetType(petId);
      return petType && this.isPetLevelAppropriate(petType, questLevel);
    });
  }

  getSeasonalPets() {
    const currentMonth = new Date().getMonth();
    const seasonalPets = {
      winter: ['ice_elemental', 'arctic_fox', 'snow_leopard', 'winter_wolf'],
      spring: ['fairy_dragon', 'bunny', 'flower_sprite', 'spring_deer'],
      summer: ['phoenix', 'fire_elemental', 'solar_lion', 'summer_butterfly'],
      fall: ['harvest_golem', 'autumn_wolf', 'leaf_sprite', 'mushroom_familiar']
    };

    const season = Math.floor(currentMonth / 3); // 0= winter, 1= spring, etc.
    const seasons = ['winter', 'spring', 'summer', 'fall'];
    return seasonalPets[seasons[season]] || seasonalPets.spring;
  }

  isPetLevelAppropriate(petType, questLevel) {
    const petPowerLevel = Object.values(petType.baseStats).reduce((a, b) => a + b, 0);
    const appropriateRange = {
      low: { min: 30, max: 80 },
      medium: { min: 60, max: 150 },
      high: { min: 120, max: 300 },
      legendary: { min: 200, max: 500 }
    };

    const questDifficulty = questLevel <= 3 ? 'low' :
                          questLevel <= 6 ? 'medium' :
                          questLevel <= 9 ? 'high' : 'legendary';

    const range = appropriateRange[questDifficulty];
    return petPowerLevel >= range.min && petPowerLevel <= range.max;
  }

  // HELPER METHODS
  calculateTamingTime(creature, method) {
    const baseTime = 60000; // 1 minute base
    const difficultyMultiplier = {
      common: 1,
      uncommon: 1.5,
      rare: 2,
      epic: 3,
      legendary: 4
    };

    const methodMultiplier = {
      standard: 1,
      food_bait: 0.8,
      magical_aid: 1.2,
      ritual: 1.5,
      master_tamer: 2
    };

    return Math.floor(baseTime * difficultyMultiplier[creature.rarity] * methodMultiplier[method]);
  }

  getEnvironmentBonus(location, preferredHabitat) {
    const environmentMatches = {
      forest: ['forest', 'enchanted_forest', 'dark_forest'],
      mountain: ['mountain', 'mountain_peak', 'volcano'],
      desert: ['desert'],
      arctic: ['arctic', 'tundra'],
      urban: ['city', 'town', 'urban']
    };

    const locationType = location?.type || 'unknown';
    const preferredEnvironments = environmentMatches[preferredHabitat] || [];

    return preferredEnvironments.includes(locationType) ? 0.1 : 0;
  }

  getLocationSummoningBonus(location, ritualType) {
    const locationBonuses = {
      magic_tower: { basic_familiar: 0.1, elemental_binding: 0.15 },
      graveyard: { dark_pact: 0.2 },
      church: { celestial_summoning: 0.15 },
      dragon_lair: { dragon_egg_hatching: 0.1 },
      elemental_plane: { elemental_binding: 0.25 }
    };

    const locationType = location?.type || 'unknown';
    return locationBonuses[locationType]?.[ritualType] || 0;
  }

  calculateTamingBondingBonus(method) {
    const bonuses = {
      standard: 5,
      food_bait: 8,
      magical_aid: 10,
      ritual: 15,
      master_tamer: 20
    };
    return bonuses[method] || 5;
  }

  async getCreature(creatureId) {
    // This would interface with the creature/database system
    // For now, return a mock creature
    const petType = this.petDatabase.getPetType(creatureId);
    if (!petType) return null;

    return {
      id: creatureId,
      ...petType,
      isWild: true,
      difficulty: petType.rarity
    };
  }

  async consumeOfferings(playerId, offerings) {
    const player = await this.playerManager.getPlayer(playerId);
    if (!player.inventory) return;

    for (const offering of offerings) {
      const itemIndex = player.inventory.findIndex(item => item.id === offering.id);
      if (itemIndex >= 0) {
        player.inventory[itemIndex].quantity -= offering.quantity;
        if (player.inventory[itemIndex].quantity <= 0) {
          player.inventory.splice(itemIndex, 1);
        }
      }
    }

    await this.playerManager.updatePlayer(playerId, player);
  }
}

module.exports = PetAcquisition;