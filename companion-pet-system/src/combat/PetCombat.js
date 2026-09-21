/**
 * Pet combat system with unique abilities, support capabilities,
 * utility skills, and tournament mechanics
 */

class PetCombat {
  constructor(petDatabase, world) {
    this.petDatabase = petDatabase;
    this.world = world;
    this.activeBattles = new Map();
    this.tournamentManager = new TournamentManager();
    this.abilityCooldowns = new Map();
    this.combatEffects = new Map();
    this.battlePets = new Set();
  }

  // COMBAT INITIALIZATION
  enterBattle(pet, battleType = 'normal', opponents = []) {
    if (!this.canEnterCombat(pet)) {
      return { success: false, reason: 'cannot_enter_combat' };
    }

    const battleId = this.generateBattleId();
    const battle = {
      id: battleId,
      type: battleType,
      participants: [pet.id, ...opponents.map(op => op.id)],
      startTime: Date.now(),
      currentTurn: 0,
      turnOrder: this.determineTurnOrder([pet, ...opponents]),
      status: 'active',
      environment: this.world.getCurrentEnvironment(),
      rules: this.getBattleRules(battleType)
    };

    this.activeBattles.set(battleId, battle);
    this.battlePets.add(pet.id);

    // Initialize combat state for pet
    this.initializeCombatState(pet, battle);

    return {
      success: true,
      battleId,
      turnOrder: battle.turnOrder,
      opponentCount: opponents.length
    };
  }

  canEnterCombat(pet) {
    // Check if pet is able to fight
    if (pet.currentHealth <= 0) {
      return false;
    }

    if (pet.energy < 20) {
      return false;
    }

    if (this.battlePets.has(pet.id)) {
      return false;
    }

    // Check if pet has combat abilities
    const combatAbilities = this.getCombatAbilities(pet);
    return combatAbilities.length > 0;
  }

  initializeCombatState(pet, battle) {
    pet.combatState = {
      battleId: battle.id,
      position: this.getRandomPosition(),
      currentHealth: pet.currentHealth,
      currentEnergy: pet.energy,
      statusEffects: [],
      activeBuffs: [],
      activeDebuffs: [],
      lastAction: null,
      actionHistory: [],
      combatStats: this.calculateCombatStats(pet),
      positionHistory: []
    };

    // Reset ability cooldowns
    this.abilityCooldowns.set(pet.id, new Map());

    // Apply environmental bonuses
    this.applyEnvironmentalCombatBonuses(pet, battle.environment);
  }

  determineTurnOrder(participants) {
    // Sort by speed stat with some randomness
    const shuffled = [...participants].sort(() => Math.random() - 0.5);
    return shuffled.sort((a, b) => {
      const speedA = a.stats.speed + Math.random() * 10;
      const speedB = b.stats.speed + Math.random() * 10;
      return speedB - speedA;
    });
  }

  getBattleRules(battleType) {
    const rules = {
      normal: {
        timeLimit: 300000, // 5 minutes
        allowItems: true,
        allowFlee: true,
        deathPenalty: false,
        reviveChance: 0.1
      },
      tournament: {
        timeLimit: 180000, // 3 minutes
        allowItems: false,
        allowFlee: false,
        deathPenalty: false,
        reviveChance: 0
      },
      boss: {
        timeLimit: 600000, // 10 minutes
        allowItems: true,
        allowFlee: true,
        deathPenalty: true,
        reviveChance: 0.2
      },
      pvp: {
        timeLimit: 240000, // 4 minutes
        allowItems: true,
        allowFlee: false,
        deathPenalty: false,
        reviveChance: 0
      }
    };

    return rules[battleType] || rules.normal;
  }

  // COMBAT ACTIONS
  performAction(pet, action, target = null) {
    if (!pet.combatState) {
      return { success: false, reason: 'not_in_combat' };
    }

    const battle = this.activeBattles.get(pet.combatState.battleId);
    if (!battle || battle.status !== 'active') {
      return { success: false, reason: 'battle_not_active' };
    }

    // Check if it's pet's turn
    const currentTurnPet = battle.turnOrder[battle.currentTurn % battle.turnOrder.length];
    if (currentTurnPet.id !== pet.id) {
      return { success: false, reason: 'not_your_turn' };
    }

    // Validate action
    const validationResult = this.validateAction(pet, action, target);
    if (!validationResult.valid) {
      return { success: false, reason: validationResult.reason };
    }

    // Execute action
    const result = this.executeCombatAction(pet, action, target, battle);

    // Record action
    pet.combatState.lastAction = {
      action,
      target: target?.id,
      timestamp: Date.now(),
      result: result.success
    };
    pet.combatState.actionHistory.push(pet.combatState.lastAction);

    // Update turn
    battle.currentTurn++;

    // Check battle end conditions
    this.checkBattleEndConditions(battle);

    return result;
  }

  validateAction(pet, action, target) {
    // Check energy requirements
    const ability = this.getAbility(action);
    if (ability && ability.energyCost > pet.combatState.currentEnergy) {
      return { valid: false, reason: 'insufficient_energy' };
    }

    // Check cooldowns
    const cooldowns = this.abilityCooldowns.get(pet.id);
    if (cooldowns && cooldowns.has(action)) {
      const remainingCooldown = cooldowns.get(action) - Date.now();
      if (remainingCooldown > 0) {
        return { valid: false, reason: 'ability_on_cooldown', remainingTime: remainingCooldown };
      }
    }

    // Validate target
    if (ability && ability.requiresTarget && !target) {
      return { valid: false, reason: 'target_required' };
    }

    // Check range
    if (target && ability && ability.range) {
      const distance = this.calculateDistance(pet, target);
      if (distance > ability.range) {
        return { valid: false, reason: 'target_out_of_range' };
      }
    }

    return { valid: true };
  }

  executeCombatAction(pet, action, target, battle) {
    const ability = this.getAbility(action);
    if (!ability) {
      return { success: false, reason: 'invalid_ability' };
    }

    // Consume energy
    pet.combatState.currentEnergy -= ability.energyCost;

    // Set cooldown
    const cooldowns = this.abilityCooldowns.get(pet.id) || new Map();
    cooldowns.set(action, Date.now() + (ability.cooldown || 0));
    this.abilityCooldowns.set(pet.id, cooldowns);

    // Execute ability effects
    const results = {
      success: true,
      action,
      target: target?.id,
      effects: [],
      damage: 0,
      healing: 0,
      statusEffects: [],
      critical: false,
      missed: false
    };

    try {
      // Calculate hit chance
      const hitChance = this.calculateHitChance(pet, target, ability);
      if (Math.random() > hitChance) {
        results.missed = true;
        return results;
      }

      // Calculate critical chance
      const criticalChance = this.calculateCriticalChance(pet, ability);
      const isCritical = Math.random() < criticalChance;
      results.critical = isCritical;

      // Apply ability effects
      this.applyAbilityEffects(pet, target, ability, results, battle);

      // Apply status effects
      if (ability.statusEffects) {
        this.applyStatusEffects(pet, target, ability.statusEffects, results);
      }

      // Generate combat memory
      pet.addMemory({
        type: 'combat_action',
        content: `Used ${action} in combat ${isCritical ? '(critical!)' : ''} ${results.missed ? '(missed)' : ''}`,
        importance: 2
      });

    } catch (error) {
      results.success = false;
      results.error = error.message;
    }

    return results;
  }

  calculateHitChance(attacker, defender, ability) {
    let baseChance = 0.85; // 85% base hit chance

    // Accuracy vs Evasion
    const accuracy = attacker.combatState.combatStats.accuracy || 100;
    const evasion = defender?.combatState.combatStats.evasion || 0;
    const accuracyModifier = (accuracy - evasion) / 100;

    // Ability accuracy modifier
    const abilityAccuracy = ability.accuracy || 1.0;

    // Distance modifier
    const distance = defender ? this.calculateDistance(attacker, defender) : 0;
    const distanceModifier = ability.range ? Math.max(0.5, 1 - (distance / (ability.range * 2))) : 1.0;

    // Status effect modifiers
    const statusModifier = this.getStatusAccuracyModifier(attacker, defender);

    const finalChance = baseChance + accuracyModifier + (abilityAccuracy - 1) + (distanceModifier - 1) + statusModifier;

    return Math.max(0.1, Math.min(0.95, finalChance));
  }

  calculateCriticalChance(attacker, ability) {
    let baseChance = 0.05; // 5% base critical chance

    // Critical rate from stats
    const critRate = attacker.combatState.combatStats.criticalRate || 0;
    baseChance += critRate;

    // Ability critical modifier
    if (ability.criticalBonus) {
      baseChance += ability.criticalBonus;
    }

    // Emotional state affects critical chance
    if (attacker.currentEmotion === 'excited') {
      baseChance += 0.1;
    } else if (attacker.currentEmotion === 'angry') {
      baseChance += 0.05;
    }

    return Math.max(0, Math.min(0.5, baseChance));
  }

  applyAbilityEffects(attacker, target, ability, results, battle) {
    const power = this.calculateAbilityPower(attacker, ability, results.critical);

    // Damage effects
    if (ability.damage) {
      const damage = this.calculateDamage(attacker, target, ability.damage, power);
      results.damage = damage;
      results.effects.push(`dealt ${damage} damage`);

      if (target) {
        this.applyDamage(target, damage);
      }
    }

    // Healing effects
    if (ability.healing) {
      const healing = this.calculateHealing(attacker, target, ability.healing, power);
      results.healing = healing;
      results.effects.push(`healed ${healing} health`);

      if (target) {
        this.applyHealing(target, healing);
      }
    }

    // Special effects
    if (ability.specialEffects) {
      for (const effect of ability.specialEffects) {
        this.applySpecialEffect(attacker, target, effect, results, battle);
      }
    }

    // Area of effect
    if (ability.aoe && battle) {
      this.applyAOEEffects(attacker, ability, battle, results);
    }
  }

  calculateAbilityPower(attacker, ability, isCritical) {
    let power = 1.0;

    // Base power from attack stat
    power += attacker.combatState.combatStats.attack / 100;

    // Ability power multiplier
    if (ability.powerMultiplier) {
      power *= ability.powerMultiplier;
    }

    // Critical damage bonus
    if (isCritical) {
      power *= 1.5 + (attacker.combatState.combatStats.criticalDamage || 0);
    }

    // Emotional state affects power
    const emotionalPower = this.getEmotionalPowerModifier(attacker.currentEmotion);
    power *= emotionalPower;

    // Status effect modifiers
    const statusPower = this.getStatusPowerModifier(attacker);
    power *= statusPower;

    return power;
  }

  getEmotionalPowerModifier(emotion) {
    const modifiers = {
      ecstatic: 1.2,
      excited: 1.15,
      angry: 1.1,
      protective: 1.05,
      happy: 1.0,
      content: 1.0,
      neutral: 1.0,
      unhappy: 0.9,
      anxious: 0.85,
      fearful: 0.8,
      sad: 0.8
    };
    return modifiers[emotion] || 1.0;
  }

  calculateDamage(attacker, target, damageType, power) {
    let baseDamage = damageType.base || 10;

    // Apply attacker's attack stat
    baseDamage += attacker.combatState.combatStats.attack;

    // Apply power multiplier
    baseDamage *= power;

    // Apply defender's defense
    if (target) {
      const defense = target.combatState.combatStats.defense;
      baseDamage = Math.max(1, baseDamage - defense);

      // Apply damage type effectiveness
      const effectiveness = this.calculateDamageEffectiveness(damageType.type, target);
      baseDamage *= effectiveness;
    }

    // Apply randomness
    const randomFactor = 0.8 + Math.random() * 0.4; // 80-120% of base damage
    baseDamage *= randomFactor;

    return Math.floor(baseDamage);
  }

  calculateHealing(attacker, target, healingType, power) {
    let baseHealing = healingType.base || 10;

    // Apply healer's intelligence or support stat
    const supportStat = attacker.combatState.combatStats.intelligence ||
                       attacker.combatState.combatStats.support || 50;
    baseHealing += supportStat / 2;

    // Apply power multiplier
    baseHealing *= power;

    // Apply target's healing received bonus
    if (target) {
      const healingReceived = target.combatState.combatStats.healingReceived || 1.0;
      baseHealing *= healingReceived;
    }

    // Apply randomness
    const randomFactor = 0.9 + Math.random() * 0.2; // 90-110% of base healing
    baseHealing *= randomFactor;

    return Math.floor(baseHealing);
  }

  calculateDamageEffectiveness(damageType, target) {
    // This would check target's resistances and weaknesses
    const resistances = target.resistances || {};
    const weakness = target.weaknesses || {};

    let effectiveness = 1.0;

    if (resistances[damageType]) {
      effectiveness *= (1 - resistances[damageType]);
    }

    if (weakness[damageType]) {
      effectiveness *= (1 + weakness[damageType]);
    }

    return Math.max(0.1, effectiveness);
  }

  applyDamage(target, damage) {
    target.combatState.currentHealth = Math.max(0, target.combatState.currentHealth - damage);

    // Check if pet is defeated
    if (target.combatState.currentHealth <= 0) {
      this.handlePetDefeat(target);
    }

    // Generate damage memory
    target.addMemory({
      type: 'combat_damage',
      content: `Took ${damage} damage in combat`,
      importance: 2
    });
  }

  applyHealing(target, healing) {
    const maxHealth = target.maxHealth;
    target.combatState.currentHealth = Math.min(maxHealth, target.combatState.currentHealth + healing);

    // Generate healing memory
    target.addMemory({
      type: 'combat_healing',
      content: `Received ${healing} healing in combat`,
      importance: 2
    });
  }

  applyStatusEffects(caster, target, effects, results) {
    if (!target) return;

    for (const effect of effects) {
      const success = Math.random() < (effect.chance || 1.0);
      if (success) {
        this.applyStatusEffect(target, effect);
        results.statusEffects.push(effect.type);
      }
    }
  }

  applyStatusEffect(target, effect) {
    const statusEffect = {
      type: effect.type,
      duration: effect.duration || 30000, // 30 seconds default
      startTime: Date.now(),
      source: effect.source,
      potency: effect.potency || 1.0
    };

    target.combatState.statusEffects.push(statusEffect);

    // Apply immediate effect
    this.applyStatusEffectImmediate(target, statusEffect);
  }

  applyStatusEffectImmediate(target, effect) {
    switch (effect.type) {
      case 'burn':
        // Damage over time
        this.applyDamage(target, Math.floor(10 * effect.potency));
        break;
      case 'poison':
        // Damage over time
        this.applyDamage(target, Math.floor(5 * effect.potency));
        break;
      case 'heal':
        // Heal over time
        this.applyHealing(target, Math.floor(8 * effect.potency));
        break;
      case 'stun':
        // Cannot act
        target.combatState.stunned = true;
        break;
      case 'sleep':
        // Cannot act, but wakes on damage
        target.combatState.asleep = true;
        break;
    }
  }

  applySpecialEffect(caster, target, effect, results, battle) {
    switch (effect.type) {
      case 'knockback':
        if (target) {
          this.applyKnockback(target, effect.force);
          results.effects.push('knocked back target');
        }
        break;

      case 'pull':
        if (target) {
          this.applyPull(target, effect.force);
          results.effects.push('pulled target');
        }
        break;

      case 'teleport':
        this.applyTeleport(caster, effect.distance);
        results.effects.push('teleported');
        break;

      case 'summon':
        this.applySummon(caster, effect.summonType, battle);
        results.effects.push(`summoned ${effect.summonType}`);
        break;

      case 'transform':
        this.applyTransform(caster, effect.transformType, effect.duration);
        results.effects.push(`transformed into ${effect.transformType}`);
        break;

      case 'shield':
        this.applyShield(caster, effect.shieldAmount, effect.duration);
        results.effects.push(`gained shield`);
        break;
    }
  }

  applyAOEEffects(caster, ability, battle, results) {
    const targets = this.getAOETargets(caster, ability, battle);

    for (const target of targets) {
      if (target.id !== caster.id) {
        const aoeResults = {
          success: true,
          action: ability.id,
          target: target.id,
          damage: 0,
          healing: 0,
          critical: false,
          missed: false
        };

        this.applyAbilityEffects(caster, target, ability, aoeResults, battle);
        results.aoeHits = results.aoeHits || [];
        results.aoeHits.push(aoeResults);
      }
    }
  }

  getAOETargets(caster, ability, battle) {
    const targets = [];
    const range = ability.aoeRange || ability.range || 5;
    const maxTargets = ability.maxTargets || 5;

    for (const participantId of battle.participants) {
      if (participantId !== caster.id) {
        const target = this.getPetById(participantId);
        if (target && this.calculateDistance(caster, target) <= range) {
          targets.push(target);
          if (targets.length >= maxTargets) break;
        }
      }
    }

    return targets;
  }

  // PET ABILITIES
  getCombatAbilities(pet) {
    const allAbilities = this.getAllAbilities();
    return pet.abilities.filter(abilityId => allAbilities[abilityId] && allAbilities[abilityId].combat);
  }

  getAllAbilities() {
    return {
      // Attack abilities
      bite: {
        name: 'Bite',
        type: 'attack',
        combat: true,
        energyCost: 10,
        cooldown: 2000,
        range: 1,
        damage: { base: 15, type: 'physical' },
        accuracy: 0.9,
        criticalBonus: 0.05
      },

      claw: {
        name: 'Claw',
        type: 'attack',
        combat: true,
        energyCost: 12,
        cooldown: 2500,
        range: 1,
        damage: { base: 18, type: 'physical' },
        accuracy: 0.85,
        criticalBonus: 0.1
      },

      fire_breath: {
        name: 'Fire Breath',
        type: 'attack',
        combat: true,
        energyCost: 25,
        cooldown: 8000,
        range: 5,
        damage: { base: 30, type: 'fire' },
        accuracy: 0.8,
        statusEffects: [
          { type: 'burn', chance: 0.3, duration: 10000, potency: 1.5 }
        ],
        aoe: true,
        aoeRange: 3
      },

      ice_shard: {
        name: 'Ice Shard',
        type: 'attack',
        combat: true,
        energyCost: 20,
        cooldown: 6000,
        range: 8,
        damage: { base: 25, type: 'ice' },
        accuracy: 0.9,
        statusEffects: [
          { type: 'freeze', chance: 0.2, duration: 5000 }
        ]
      },

      shadow_blend: {
        name: 'Shadow Blend',
        type: 'utility',
        combat: true,
        energyCost: 15,
        cooldown: 10000,
        range: 0,
        specialEffects: [
          { type: 'stealth', duration: 8000 }
        ]
      },

      // Support abilities
      healing_aura: {
        name: 'Healing Aura',
        type: 'support',
        combat: true,
        energyCost: 30,
        cooldown: 15000,
        range: 0,
        healing: { base: 20, type: 'holy' },
        aoe: true,
        aoeRange: 5
      },

      protective_barrier: {
        name: 'Protective Barrier',
        type: 'support',
        combat: true,
        energyCost: 25,
        cooldown: 12000,
        range: 3,
        specialEffects: [
          { type: 'shield', shieldAmount: 50, duration: 10000 }
        ]
      },

      battle_roar: {
        name: 'Battle Roar',
        type: 'support',
        combat: true,
        energyCost: 20,
        cooldown: 20000,
        range: 0,
        specialEffects: [
          { type: 'buff', buffType: 'attack', buffAmount: 10, duration: 15000 }
        ],
        aoe: true,
        aoeRange: 8
      },

      // Ultimate abilities
      cataclysm_breath: {
        name: 'Cataclysm Breath',
        type: 'ultimate',
        combat: true,
        energyCost: 50,
        cooldown: 60000,
        range: 10,
        damage: { base: 100, type: 'dragon' },
        accuracy: 0.95,
        criticalBonus: 0.2,
        powerMultiplier: 2.0,
        aoe: true,
        aoeRange: 6,
        statusEffects: [
          { type: 'burn', chance: 0.5, duration: 15000, potency: 2.0 },
          { type: 'stun', chance: 0.3, duration: 3000 }
        ]
      },

      rebirth_flame: {
        name: 'Rebirth Flame',
        type: 'ultimate',
        combat: true,
        energyCost: 40,
        cooldown: 120000,
        range: 0,
        healing: { base: 200, type: 'holy' },
        specialEffects: [
          { type: 'revive', condition: 'defeated' },
          { type: 'immunity', duration: 10000 }
        ],
        aoe: true,
        aoeRange: 8
      }
    };
  }

  getAbility(abilityId) {
    const abilities = this.getAllAbilities();
    return abilities[abilityId] || null;
  }

  // UTILITY SKILLS
  getUtilitySkills(pet) {
    const utilitySkills = {
      tracking: {
        name: 'Tracking',
        type: 'utility',
        description: 'Can track enemies and find hidden paths',
        effectiveness: () => pet.stats.intelligence + pet.level * 2
      },

      scouting: {
        name: 'Scouting',
        type: 'utility',
        description: 'Can scout areas and reveal hidden dangers',
        effectiveness: () => pet.stats.speed + pet.level
      },

      crafting: {
        name: 'Crafting',
        type: 'utility',
        description: 'Can assist in crafting and create pet-specific items',
        effectiveness: () => pet.stats.intelligence + pet.level * 1.5
      },

      foraging: {
        name: 'Foraging',
        type: 'utility',
        description: 'Can find food and resources in the wild',
        effectiveness: () => pet.stats.intelligence + pet.bonding
      },

      mount: {
        name: 'Mount',
        type: 'utility',
        description: 'Can be ridden as a mount (if large enough)',
        available: () => pet.size > 1.5 && pet.traits.includes('rideable'),
        effectiveness: () => pet.stats.speed + pet.stats.health / 10
      },

      treasure_sense: {
        name: 'Treasure Sense',
        type: 'utility',
        description: 'Can detect nearby treasure and valuable items',
        effectiveness: () => pet.stats.intelligence + pet.level * 3
      },

      night_vision: {
        name: 'Night Vision',
        type: 'utility',
        description: 'Can see in the dark',
        available: () => pet.traits.includes('nocturnal') || pet.abilities.includes('night_vision'),
        effectiveness: () => 100 // Always effective when available
      },

      camouflage: {
        name: 'Camouflage',
        type: 'utility',
        description: 'Can blend with environment for stealth',
        effectiveness: () => pet.stats.speed + pet.level * 2
      }
    };

    // Filter and return available utility skills for this pet
    const availableSkills = {};
    for (const [skillId, skill] of Object.entries(utilitySkills)) {
      if (!skill.available || skill.available()) {
        availableSkills[skillId] = skill;
      }
    }

    return availableSkills;
  }

  performUtilityAction(pet, skillId, context = {}) {
    const utilitySkills = this.getUtilitySkills(pet);
    const skill = utilitySkills[skillId];

    if (!skill) {
      return { success: false, reason: 'skill_not_available' };
    }

    // Check energy requirements
    const energyCost = this.getUtilitySkillEnergyCost(skillId);
    if (pet.energy < energyCost) {
      return { success: false, reason: 'insufficient_energy' };
    }

    // Execute utility action
    const result = this.executeUtilityAction(pet, skill, context);

    if (result.success) {
      pet.energy -= energyCost;

      // Add memory
      pet.addMemory({
        type: 'utility_action',
        content: `Used ${skill.name}: ${result.description || 'completed successfully'}`,
        importance: 1
      });
    }

    return result;
  }

  executeUtilityAction(pet, skill, context) {
    const effectiveness = skill.effectiveness();
    const baseSuccessChance = 0.7 + (effectiveness / 200);

    switch (skillId) {
      case 'tracking':
        return this.executeTracking(pet, context, effectiveness, baseSuccessChance);

      case 'scouting':
        return this.executeScouting(pet, context, effectiveness, baseSuccessChance);

      case 'crafting':
        return this.executeCrafting(pet, context, effectiveness, baseSuccessChance);

      case 'foraging':
        return this.executeForaging(pet, context, effectiveness, baseSuccessChance);

      case 'mount':
        return this.executeMount(pet, context, effectiveness);

      case 'treasure_sense':
        return this.executeTreasureSense(pet, context, effectiveness, baseSuccessChance);

      default:
        return { success: true, description: 'Utility action completed' };
    }
  }

  executeTracking(pet, context, effectiveness, successChance) {
    const target = context.target;
    if (!target) {
      return { success: false, reason: 'no_target' };
    }

    const success = Math.random() < successChance;
    if (success) {
      const trackingInfo = {
        direction: this.calculateDirection(pet, target),
        distance: this.calculateDistance(pet, target),
        confidence: Math.min(1.0, effectiveness / 100),
        lastSeen: Date.now()
      };

      return {
        success: true,
        description: `Successfully tracked ${target.name || 'target'}`,
        trackingInfo
      };
    } else {
      return {
        success: false,
        reason: 'tracking_failed',
        description: 'Lost the trail'
      };
    }
  }

  executeScouting(pet, context, effectiveness, successChance) {
    const area = context.area;
    const success = Math.random() < successChance;

    if (success) {
      const discoveries = this.generateScoutingDiscoveries(area, effectiveness);
      return {
        success: true,
        description: `Discovered ${discoveries.length} points of interest`,
        discoveries
      };
    } else {
      return {
        success: false,
        reason: 'scouting_failed',
        description: 'Nothing unusual found'
      };
    }
  }

  executeCrafting(pet, context, effectiveness, successChance) {
    const recipe = context.recipe;
    if (!recipe) {
      return { success: false, reason: 'no_recipe' };
    }

    const success = Math.random() < successChance;
    if (success) {
      const craftedItem = this.craftItem(recipe, effectiveness);
      return {
        success: true,
        description: `Successfully crafted ${craftedItem.name}`,
        item: craftedItem
      };
    } else {
      return {
        success: false,
        reason: 'crafting_failed',
        description: 'Crafting attempt failed'
      };
    }
  }

  executeForaging(pet, context, effectiveness, successChance) {
    const success = Math.random() < successChance;
    if (success) {
      const foundItems = this.generateForagedItems(effectiveness);
      return {
        success: true,
        description: `Found ${foundItems.length} items`,
        items: foundItems
      };
    } else {
      return {
        success: false,
        reason: 'foraging_failed',
        description: 'Nothing edible found'
      };
    }
  }

  executeMount(pet, context, effectiveness) {
    if (!this.getUtilitySkills(pet).mount.available()) {
      return { success: false, reason: 'cannot_be_mounted' };
    }

    const rider = context.rider;
    if (!rider) {
      return { success: false, reason: 'no_rider' };
    }

    // Set mount state
    pet.isMount = true;
    pet.rider = rider;

    return {
      success: true,
      description: `${pet.name} is now being ridden`,
      speed: effectiveness
    };
  }

  executeTreasureSense(pet, context, effectiveness, successChance) {
    const success = Math.random() < successChance;
    if (success) {
      const treasure = this.detectNearbyTreasure(effectiveness);
      return {
        success: true,
        description: `Detected treasure nearby`,
        treasure
      };
    } else {
      return {
        success: false,
        reason: 'no_treasure_detected',
        description: 'No treasure detected'
      };
    }
  }

  // TOURNAMENT SYSTEM
  createTournament(type, level, rules = {}) {
    return this.tournamentManager.createTournament(type, level, rules);
  }

  enterTournament(pet, tournamentId) {
    return this.tournamentManager.enterPet(pet, tournamentId);
  }

  getTournamentStatus(tournamentId) {
    return this.tournamentManager.getTournamentStatus(tournamentId);
  }

  // HELPER METHODS
  generateBattleId() {
    return 'battle_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
  }

  getRandomPosition() {
    return {
      x: Math.random() * 100,
      y: Math.random() * 100,
      z: 0
    };
  }

  calculateDistance(entity1, entity2) {
    if (!entity1.combatState || !entity2.combatState) return 999;

    const pos1 = entity1.combatState.position;
    const pos2 = entity2.combatState.position;

    const dx = pos1.x - pos2.x;
    const dy = pos1.y - pos2.y;
    const dz = pos1.z - pos2.z;

    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  calculateDirection(from, to) {
    const angle = Math.atan2(
      to.combatState.position.y - from.combatState.position.y,
      to.combatState.position.x - from.combatState.position.x
    );
    return angle * (180 / Math.PI); // Convert to degrees
  }

  calculateCombatStats(pet) {
    return {
      attack: pet.stats.attack + this.getEquipmentStatBonus(pet, 'attack'),
      defense: pet.stats.defense + this.getEquipmentStatBonus(pet, 'defense'),
      speed: pet.stats.speed + this.getEquipmentStatBonus(pet, 'speed'),
      accuracy: 100 + (pet.stats.intelligence / 2),
      evasion: pet.stats.speed / 2,
      criticalRate: 0.05 + (pet.stats.intelligence / 1000),
      criticalDamage: 0.5 + (pet.stats.attack / 200),
      support: pet.stats.intelligence + this.getEquipmentStatBonus(pet, 'intelligence'),
      healingReceived: 1.0 + (this.getEquipmentStatBonus(pet, 'healing') / 100)
    };
  }

  getEquipmentStatBonus(pet, stat) {
    let bonus = 0;
    for (const equipment of Object.values(pet.equipment)) {
      if (equipment && equipment.stats && equipment.stats[stat]) {
        bonus += equipment.stats[stat];
      }
    }
    return bonus;
  }

  applyEnvironmentalCombatBonuses(pet, environment) {
    // Apply environment-specific combat bonuses
    switch (environment.location.type) {
      case 'volcano':
        if (pet.traits.includes('fire_affinity')) {
          pet.combatState.combatStats.attack *= 1.2;
        }
        break;
      case 'arctic':
        if (pet.traits.includes('ice_affinity')) {
          pet.combatState.combatStats.defense *= 1.2;
        }
        break;
      case 'forest':
        if (pet.category === 'animal') {
          pet.combatState.combatStats.speed *= 1.1;
        }
        break;
    }
  }

  getStatusAccuracyModifier(attacker, defender) {
    let modifier = 0;

    // Check status effects
    if (attacker.combatState.statusEffects.some(e => e.type === 'accuracy_boost')) {
      modifier += 0.2;
    }
    if (attacker.combatState.statusEffects.some(e => e.type === 'blind')) {
      modifier -= 0.3;
    }
    if (defender?.combatState.statusEffects.some(e => e.type === 'evasion_boost')) {
      modifier -= 0.2;
    }

    return modifier;
  }

  getStatusPowerModifier(attacker) {
    let modifier = 1.0;

    if (attacker.combatState.statusEffects.some(e => e.type === 'power_boost')) {
      modifier *= 1.3;
    }
    if (attacker.combatState.statusEffects.some(e => e.type === 'weakened')) {
      modifier *= 0.7;
    }

    return modifier;
  }

  handlePetDefeat(pet) {
    pet.combatState.defeated = true;
    pet.combatState.defeatTime = Date.now();

    // Add defeat memory
    pet.addMemory({
      type: 'combat_defeat',
      content: 'Was defeated in combat',
      importance: 4
    });

    // Remove from battle
    this.battlePets.delete(pet.id);

    // Check for revive chance
    const battle = this.activeBattles.get(pet.combatState.battleId);
    if (battle && Math.random() < battle.rules.reviveChance) {
      this.revivePet(pet);
    }
  }

  revivePet(pet) {
    pet.combatState.defeated = false;
    pet.combatState.currentHealth = pet.maxHealth * 0.3; // Revive with 30% health
    pet.combatState.currentEnergy = pet.energy * 0.5; // 50% energy

    pet.addMemory({
      type: 'combat_revive',
      content: 'Was revived during combat',
      importance: 3
    });
  }

  checkBattleEndConditions(battle) {
    const activeParticipants = battle.participants.filter(participantId => {
      const pet = this.getPetById(participantId);
      return pet && !pet.combatState.defeated;
    });

    // Check if battle should end
    if (activeParticipants.length <= 1) {
      this.endBattle(battle, activeParticipants[0]);
    } else if (Date.now() - battle.startTime > battle.rules.timeLimit) {
      this.endBattle(battle, null, 'time_limit');
    }
  }

  endBattle(battle, winnerId, reason = 'victory') {
    battle.status = 'ended';
    battle.endTime = Date.now();
    battle.winner = winnerId;
    battle.endReason = reason;

    // Clean up combat states
    for (const participantId of battle.participants) {
      const pet = this.getPetById(participantId);
      if (pet && pet.combatState) {
        this.cleanupCombatState(pet, battle);
        this.battlePets.delete(participantId);
      }
    }

    // Generate battle memories
    for (const participantId of battle.participants) {
      const pet = this.getPetById(participantId);
      if (pet) {
        pet.addMemory({
          type: 'combat_end',
          content: `Battle ended: ${reason}${winnerId === participantId ? ' (victory!)' : ''}`,
          importance: 3
        });
      }
    }
  }

  cleanupCombatState(pet, battle) {
    // Update pet stats based on combat performance
    if (battle.winner === pet.id) {
      pet.gainExperience(50);
      pet.bonding = Math.min(100, pet.bonding + 5);
    } else {
      pet.gainExperience(10);
    }

    // Clean up combat state
    delete pet.combatState;
    this.abilityCooldowns.delete(pet.id);
  }

  getPetById(petId) {
    // This would get pet from the pet manager
    return null; // Placeholder
  }

  // Placeholder methods for utility actions
  generateScoutingDiscoveries(area, effectiveness) {
    return []; // Placeholder
  }

  craftItem(recipe, effectiveness) {
    return null; // Placeholder
  }

  generateForagedItems(effectiveness) {
    return []; // Placeholder
  }

  detectNearbyTreasure(effectiveness) {
    return null; // Placeholder
  }

  getUtilitySkillEnergyCost(skillId) {
    const costs = {
      tracking: 15,
      scouting: 20,
      crafting: 25,
      foraging: 10,
      treasure_sense: 30
    };
    return costs[skillId] || 10;
  }

  applyKnockback(target, force) {
    // Implementation for knockback physics
  }

  applyPull(target, force) {
    // Implementation for pull physics
  }

  applyTeleport(pet, distance) {
    // Implementation for teleportation
  }

  applySummon(caster, summonType, battle) {
    // Implementation for summoning
  }

  applyTransform(pet, transformType, duration) {
    // Implementation for transformation
  }

  applyShield(pet, shieldAmount, duration) {
    // Implementation for shielding
  }
}

// Tournament Manager Class
class TournamentManager {
  constructor() {
    this.tournaments = new Map();
    this.activeTournaments = new Map();
    this.tournamentHistory = new Map();
  }

  createTournament(type, level, rules = {}) {
    const tournamentId = this.generateTournamentId();
    const tournament = {
      id: tournamentId,
      type: type,
      level: level,
      rules: {
        maxParticipants: rules.maxParticipants || 16,
        petLevelRange: rules.petLevelRange || [level * 10, level * 20],
        allowedTypes: rules.allowedTypes || 'all',
        equipmentAllowed: rules.equipmentAllowed || false,
        healingAllowed: rules.healingAllowed || false,
        reviveAllowed: rules.reviveAllowed || false
      },
      participants: [],
      brackets: this.generateBrackets(rules.maxParticipants || 16),
      currentRound: 0,
      status: 'registration',
      startTime: null,
      endTime: null,
      winner: null,
      prizes: this.generateTournamentPrizes(type, level)
    };

    this.tournaments.set(tournamentId, tournament);
    this.activeTournaments.set(tournamentId, tournament);

    return {
      success: true,
      tournamentId,
      tournament
    };
  }

  enterPet(pet, tournamentId) {
    const tournament = this.tournaments.get(tournamentId);
    if (!tournament) {
      return { success: false, reason: 'tournament_not_found' };
    }

    if (tournament.status !== 'registration') {
      return { success: false, reason: 'registration_closed' };
    }

    if (tournament.participants.length >= tournament.rules.maxParticipants) {
      return { success: false, reason: 'tournament_full' };
    }

    // Validate pet eligibility
    const eligibility = this.checkPetEligibility(pet, tournament);
    if (!eligibility.eligible) {
      return { success: false, reason: eligibility.reason };
    }

    // Register pet
    const registration = {
      petId: pet.id,
      petName: pet.name,
      ownerId: pet.ownerId,
      registrationTime: Date.now(),
      initialStats: { ...pet.stats },
      initialLevel: pet.level
    };

    tournament.participants.push(registration);

    return {
      success: true,
      tournamentId,
      participantCount: tournament.participants.length
    };
  }

  checkPetEligibility(pet, tournament) {
    // Check level range
    const [minLevel, maxLevel] = tournament.rules.petLevelRange;
    if (pet.level < minLevel || pet.level > maxLevel) {
      return { eligible: false, reason: 'level_out_of_range', required: [minLevel, maxLevel] };
    }

    // Check pet type restrictions
    if (tournament.rules.allowedTypes !== 'all') {
      if (!tournament.rules.allowedTypes.includes(pet.typeId)) {
        return { eligible: false, reason: 'pet_type_not_allowed' };
      }
    }

    // Check if pet is already in tournament
    for (const tournament of this.tournaments.values()) {
      if (tournament.participants.some(p => p.petId === pet.id)) {
        return { eligible: false, reason: 'already_registered' };
      }
    }

    return { eligible: true };
  }

  startTournament(tournamentId) {
    const tournament = this.tournaments.get(tournamentId);
    if (!tournament) {
      return { success: false, reason: 'tournament_not_found' };
    }

    if (tournament.participants.length < 2) {
      return { success: false, reason: 'insufficient_participants' };
    }

    tournament.status = 'active';
    tournament.startTime = Date.now();
    tournament.currentRound = 1;

    // Generate first round matchups
    this.generateRoundMatchups(tournament);

    return { success: true, tournament };
  }

  generateBrackets(maxParticipants) {
    const bracketSize = Math.pow(2, Math.ceil(Math.log2(maxParticipants)));
    const brackets = [];

    for (let round = 1; round <= Math.log2(bracketSize); round++) {
      const matchesInRound = bracketSize / Math.pow(2, round);
      brackets.push({
        round: round,
        matches: Array(matchesInRound).fill(null).map((_, index) => ({
          matchId: `${round}-${index}`,
          participant1: null,
          participant2: null,
          winner: null,
          status: 'pending'
        }))
      });
    }

    return brackets;
  }

  generateRoundMatchups(tournament) {
    const currentRound = tournament.brackets[tournament.currentRound - 1];
    const participants = this.getCurrentRoundParticipants(tournament);

    // Shuffle participants for random matchups
    const shuffled = participants.sort(() => Math.random() - 0.5);

    // Assign to matches
    for (let i = 0; i < shuffled.length; i += 2) {
      const matchIndex = Math.floor(i / 2);
      if (matchIndex < currentRound.matches.length) {
        currentRound.matches[matchIndex].participant1 = shuffled[i];
        currentRound.matches[matchIndex].participant2 = shuffled[i + 1] || null;
        currentRound.matches[matchIndex].status = 'ready';
      }
    }
  }

  getCurrentRoundParticipants(tournament) {
    if (tournament.currentRound === 1) {
      return tournament.participants;
    } else {
      // Get winners from previous round
      const previousRound = tournament.brackets[tournament.currentRound - 2];
      return previousRound.matches
        .filter(match => match.winner)
        .map(match => match.winner);
    }
  }

  reportMatchResult(tournamentId, matchId, winnerId, battleDetails = {}) {
    const tournament = this.tournaments.get(tournamentId);
    if (!tournament) {
      return { success: false, reason: 'tournament_not_found' };
    }

    const match = this.findMatch(tournament, matchId);
    if (!match) {
      return { success: false, reason: 'match_not_found' };
    }

    // Record result
    match.winner = this.findParticipantById(tournament, winnerId);
    match.status = 'completed';
    match.endTime = Date.now();
    match.battleDetails = battleDetails;

    // Check if round is complete
    const currentRound = tournament.brackets[tournament.currentRound - 1];
    const roundComplete = currentRound.matches.every(match => match.status === 'completed');

    if (roundComplete) {
      if (tournament.currentRound < tournament.brackets.length) {
        // Advance to next round
        tournament.currentRound++;
        this.generateRoundMatchups(tournament);
      } else {
        // Tournament complete
        this.completeTournament(tournament);
      }
    }

    return { success: true, match, tournament };
  }

  findMatch(tournament, matchId) {
    for (const round of tournament.brackets) {
      const match = round.matches.find(m => m.matchId === matchId);
      if (match) return match;
    }
    return null;
  }

  findParticipantById(tournament, participantId) {
    return tournament.participants.find(p => p.petId === participantId);
  }

  completeTournament(tournament) {
    tournament.status = 'completed';
    tournament.endTime = Date.now();

    // Find winner (final match winner)
    const finalRound = tournament.brackets[tournament.brackets.length - 1];
    const finalMatch = finalRound.matches[0];
    tournament.winner = finalMatch.winner;

    // Award prizes
    this.awardTournamentPrizes(tournament);

    // Add to history
    this.tournamentHistory.set(tournament.id, { ...tournament });
    this.activeTournaments.delete(tournament.id);
  }

  generateTournamentPrizes(type, level) {
    const basePrizes = {
      gold: 1000 * level,
      experience: 500 * level,
      items: [],
      titles: []
    };

    switch (type) {
      case 'championship':
        basePrizes.gold *= 2;
        basePrizes.experience *= 1.5;
        basePrizes.items.push('trophy_' + type);
        basePrizes.titles.push('champion');
        break;
      case 'specialty':
        basePrizes.gold *= 1.5;
        basePrizes.experience *= 1.2;
        basePrizes.items.push('medal_' + type);
        break;
    }

    return basePrizes;
  }

  awardTournamentPrizes(tournament) {
    const rankings = this.calculateTournamentRankings(tournament);

    const prizeDistribution = {
      1: 1.0,    // Winner gets 100% of prizes
      2: 0.5,    // Runner up gets 50%
      3: 0.25,   // Third place gets 25%
      4: 0.1     // Fourth place gets 10%
    };

    for (const [rank, participant] of rankings.entries()) {
      const multiplier = prizeDistribution[rank + 1] || 0.05;
      const prizes = this.calculatePrizeShare(tournament.prizes, multiplier);

      // Award prizes to pet owner
      this.awardPrizesToOwner(participant.ownerId, prizes);

      // Add tournament memory to pet
      const pet = this.getPetById(participant.petId);
      if (pet) {
        pet.addMemory({
          type: 'tournament',
          content: `Achieved rank ${rank + 1} in ${tournament.type} tournament`,
          importance: 5 - rank
        });
      }
    }
  }

  calculateTournamentRankings(tournament) {
    // Simple ranking based on how far each participant got
    const rankings = [];

    for (const round of tournament.brackets) {
      for (const match of round.matches) {
        if (match.participant1 && !rankings.includes(match.participant1)) {
          rankings.push(match.participant1);
        }
        if (match.participant2 && !rankings.includes(match.participant2)) {
          rankings.push(match.participant2);
        }
      }
    }

    // Winner should be first
    if (tournament.winner) {
      const winnerIndex = rankings.indexOf(tournament.winner);
      if (winnerIndex > 0) {
        rankings.splice(winnerIndex, 1);
        rankings.unshift(tournament.winner);
      }
    }

    return rankings;
  }

  calculatePrizeShare(prizes, multiplier) {
    return {
      gold: Math.floor(prizes.gold * multiplier),
      experience: Math.floor(prizes.experience * multiplier),
      items: prizes.items.slice(0, Math.ceil(prizes.items.length * multiplier)),
      titles: multiplier >= 1.0 ? prizes.titles : []
    };
  }

  awardPrizesToOwner(ownerId, prizes) {
    // This would interface with the player management system
    // to award gold, experience, items, and titles
  }

  getTournamentStatus(tournamentId) {
    const tournament = this.tournaments.get(tournamentId) || this.tournamentHistory.get(tournamentId);
    if (!tournament) {
      return { success: false, reason: 'tournament_not_found' };
    }

    return {
      success: true,
      tournament: {
        id: tournament.id,
        type: tournament.type,
        status: tournament.status,
        currentRound: tournament.currentRound,
        totalRounds: tournament.brackets.length,
        participantCount: tournament.participants.length,
        startTime: tournament.startTime,
        endTime: tournament.endTime,
        winner: tournament.winner
      }
    };
  }

  generateTournamentId() {
    return 'tournament_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
  }

  getPetById(petId) {
    // This would interface with the pet management system
    return null; // Placeholder
  }
}

module.exports = PetCombat;