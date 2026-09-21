/**
 * Comprehensive evolution system for companion pets
 * Handles 5 evolution stages, skill trees, genetic traits, and special conditions
 */

class EvolutionSystem {
  constructor(petDatabase) {
    this.petDatabase = petDatabase;
    this.evolutionTrees = new Map();
    this.skillTrees = new Map();
    this.evolutionRequirements = new Map();
    this.specialEvolutions = new Map();

    this.initializeEvolutionTrees();
    this.initializeSkillTrees();
    this.initializeEvolutionRequirements();
    this.initializeSpecialEvolutions();
  }

  initializeEvolutionTrees() {
    // Define evolution paths for each pet type
    const evolutionTrees = {
      wolf: {
        stages: [
          { name: 'Pup', level: 1, requirements: { level: 1 }, visualChanges: [] },
          { name: 'Young Wolf', level: 10, requirements: { level: 10, bonding: 20 }, visualChanges: ['size_increase', 'sharper_teeth'] },
          { name: 'Alpha Wolf', level: 25, requirements: { level: 25, bonding: 50, skills: ['pack_leader'] }, visualChanges: ['alpha_mane', 'enhanced_eyes'] },
          { name: 'Dire Wolf', level: 50, requirements: { level: 50, bonding: 75, special: 'alpha_pack_trial' }, visualChanges: ['elemental_aura', 'increased_mass'] },
          { name: 'Legendary Wolf', level: 100, requirements: { level: 100, bonding: 95, legendary: 'spirit_of_the_pack' }, visualChanges: ['spirit_form', 'translucent_aura', 'elemental_wings'] }
        ]
      },

      phoenix: {
        stages: [
          { name: 'Phoenix Chick', level: 1, requirements: { level: 1 }, visualChanges: [] },
          { name: 'Young Phoenix', level: 15, requirements: { level: 15, bonding: 30 }, visualChanges: ['fire_spark', 'growing_flames'] },
          { name: 'Phoenix', level: 35, requirements: { level: 35, bonding: 60, rebirths: 1 }, visualChanges: ['full_flame_wings', 'crown_of_fire'] },
          { name: 'Solar Phoenix', level: 70, requirements: { level: 70, bonding: 85, rebirths: 3 }, visualChanges: ['solar_aura', 'golden_flames'] },
          { name: 'Celestial Phoenix', level: 100, requirements: { level: 100, bonding: 95, rebirths: 5, legendary: 'eternal_flame' }, visualChanges: ['constellation_form', 'rainbow_aura', 'divine_light'] }
        ]
      },

      dragon_whelp: {
        stages: [
          { name: 'Dragon Hatchling', level: 1, requirements: { level: 1 }, visualChanges: [] },
          { name: 'Young Dragon', level: 20, requirements: { level: 20, bonding: 40 }, visualChanges: ['wing_buds', 'horn_growth'] },
          { name: 'Adult Dragon', level: 45, requirements: { level: 45, bonding: 70, hoard_size: 1000 }, visualChanges: ['full_wings', 'elemental_breath'] },
          { name: 'Elder Dragon', level: 80, requirements: { level: 80, bonding: 90, territory: 'dragon_lair' }, visualChanges: ['ancient_scales', 'wisdom_aura'] },
          { name: 'Ancient Dragon', level: 100, requirements: { level: 100, bonding: 95, legendary: 'dragon_ancestry' }, visualChanges: ['celestial_form', 'reality_warp', 'time_aura'] }
        ]
      },

      fairy_dragon: {
        stages: [
          { name: 'Fairy Sprout', level: 1, requirements: { level: 1 }, visualChanges: [] },
          { name: 'Fairy Dragon', level: 12, requirements: { level: 12, bonding: 25 }, visualChanges: ['pixie_wings', 'magic_sparkles'] },
          { name: 'Mystic Fairy', level: 30, requirements: { level: 30, bonding: 55, magic_affinity: 50 }, visualChanges: ['enhanced_wings', 'mystic_aura'] },
          { name: 'Arcane Fairy', level: 60, requirements: { level: 60, bonding: 80, spells_learned: 10 }, visualChanges: ['arcane_symbols', 'translucent_wings'] },
          { name: 'Celestial Fairy', level: 100, requirements: { level: 100, bonding: 95, legendary: 'fairy_queen_blessing' }, visualChanges: ['starlight_form', 'rainbow_wings', 'divine_halo'] }
        ]
      }
    };

    for (const [petType, tree] of Object.entries(evolutionTrees)) {
      this.evolutionTrees.set(petType, tree);
    }
  }

  initializeSkillTrees() {
    const skillTrees = {
      // Wolf skill tree
      wolf: {
        branches: {
          alpha: {
            name: 'Alpha Leadership',
            skills: [
              { id: 'pack_leader', name: 'Pack Leader', cost: 1, effect: { leadership: 10, social_bonus: 5 } },
              { id: 'alpha_aura', name: 'Alpha Aura', cost: 2, effect: { intimidation: 15, allies_bonus: 10 } },
              { id: 'howl_of_command', name: 'Howl of Command', cost: 3, effect: { command_radius: 20, morale_boost: 20 } },
              { id: 'unity_bond', name: 'Unity Bond', cost: 4, effect: { pack_sync: 30, shared_health: 25 } },
              { id: 'legendary_alpha', name: 'Legendary Alpha', cost: 5, effect: { pack_master: 50, immortal_presence: 40 } }
            ]
          },
          hunter: {
            name: 'Hunter Instincts',
            skills: [
              { id: 'enhanced_scent', name: 'Enhanced Scent', cost: 1, effect: { tracking: 15, detection_radius: 10 } },
              { id: 'silent_prowl', name: 'Silent Prowl', cost: 2, effect: { stealth: 20, ambush_bonus: 15 } },
              { id: 'pack_coordination', name: 'Pack Coordination', cost: 3, effect: { teamwork: 25, flanking_bonus: 20 } },
              { id: 'predator_focus', name: 'Predator Focus', cost: 4, effect: { critical_strike: 30, weak_spot_detection: 25 } },
              { id: 'master_hunter', name: 'Master Hunter', cost: 5, effect: { hunt_master: 40, instant_kill_chance: 10 } }
            ]
          },
          guardian: {
            name: 'Guardian Path',
            skills: [
              { id: 'protective_instinct', name: 'Protective Instinct', cost: 1, effect: { defense_ally: 10, taunt: 5 } },
              { id: 'shield_ally', name: 'Shield Ally', cost: 2, effect: { damage_reduction_ally: 20, intercept: 15 } },
              { id: 'territorial_guard', name: 'Territorial Guard', cost: 3, effect: { home_advantage: 25, fear_aura: 20 } },
              { id: 'sacrificial_guard', name: 'Sacrificial Guard', cost: 4, effect: { damage_transfer: 35, revive_chance: 15 } },
              { id: 'eternal_guardian', name: 'Eternal Guardian', cost: 5, effect: { undying_loyalty: 50, divine_protection: 40 } }
            ]
          }
        }
      },

      // Phoenix skill tree
      phoenix: {
        branches: {
          flame: {
            name: 'Flame Mastery',
            skills: [
              { id: 'fire_resistance', name: 'Fire Resistance', cost: 1, effect: { fire_defense: 25, burn_immunity: 1 } },
              { id: 'heat_aura', name: 'Heat Aura', cost: 2, effect: { damage_aura: 10, environment_fire: 15 } },
              { id: 'inferno_wings', name: 'Inferno Wings', cost: 3, effect: { fly_damage: 20, trail_of_fire: 25 } },
              { id: 'solar_flare', name: 'Solar Flare', cost: 4, effect: { blind_enemies: 30, massive_burn: 35 } },
              { id: 'sun_incarnate', name: 'Sun Incarnate', cost: 5, effect: { solar_power: 50, day_domination: 40 } }
            ]
          },
          rebirth: {
            name: 'Rebirth Cycle',
            skills: [
              { id: 'quick_rebirth', name: 'Quick Rebirth', cost: 1, effect: { rebirth_time: -30, rebirth_health: 20 } },
              { id: 'rebirth_strength', name: 'Rebirth Strength', cost: 2, effect: { rebirth_bonus: 15, temporary_boost: 20 } },
              { id: 'phoenix_ashes', name: 'Phoenix Ashes', cost: 3, effect: { heal_allies: 25, protection_field: 20 } },
              { id: 'eternal_cycle', name: 'Eternal Cycle', cost: 4, effect: { unlimited_rebirths: 1, rebirth_power: 35 } },
              { id: 'immortal_flame', name: 'Immortal Flame', cost: 5, effect: { true_immortality: 1, flame_god: 50 } }
            ]
          },
          light: {
            name: 'Light Bearer',
            skills: [
              { id: 'light_aura', name: 'Light Aura', cost: 1, effect: { heal_aura: 5, dark_damage: 10 } },
              { id: 'purifying_flame', name: 'Purifying Flame', cost: 2, effect: { cure_curses: 20, holy_damage: 15 } },
              { id: 'dawn_bringer', name: 'Dawn Bringer', cost: 3, effect: { dispel_darkness: 25, hope_aura: 20 } },
              { id: 'solar_healing', name: 'Solar Healing', cost: 4, effect: { mass_heal: 35, revive_allies: 25 } },
              { id: 'celestial_light', name: 'Celestial Light', cost: 5, effect: { divine_healing: 50, light_mastery: 40 } }
            ]
          }
        }
      },

      // Dragon skill tree
      dragon_whelp: {
        branches: {
          might: {
            name: 'Dragon Might',
            skills: [
              { id: 'dragon_strength', name: 'Dragon Strength', cost: 1, effect: { strength: 15, carry_capacity: 20 } },
              { id: 'scale_armor', name: 'Scale Armor', cost: 2, effect: { defense: 25, damage_reduction: 15 } },
              { id: 'crushing_blow', name: 'Crushing Blow', cost: 3, effect: { damage: 30, armor_penetration: 20 } },
              { id: 'dragon_rage', name: 'Dragon Rage', cost: 4, effect: { rage_mode: 35, unstoppable: 25 } },
              { id: 'dragon_lord', name: 'Dragon Lord', cost: 5, effect: { dominion: 50, fear_aura: 40 } }
            ]
          },
          elemental: {
            name: 'Elemental Breath',
            skills: [
              { id: 'breath_weapon', name: 'Breath Weapon', cost: 1, effect: { breath_damage: 20, element_type: 'fire' } },
              { id: 'elemental_mastery', name: 'Elemental Mastery', cost: 2, effect: { element_damage: 30, resistance_all: 15 } },
              { id: 'multi_element', name: 'Multi-Element', cost: 3, effect: { dual_breath: 25, versatility: 20 } },
              { id: 'elemental_storm', name: 'Elemental Storm', cost: 4, effect: { storm_damage: 35, area_effect: 30 } },
              { id: 'primordial_force', name: 'Primordial Force', cost: 5, effect: { elemental_god: 50, reality_control: 40 } }
            ]
          },
          wisdom: {
            name: 'Ancient Wisdom',
            skills: [
              { id: 'dragon_insight', name: 'Dragon Insight', cost: 1, effect: { intelligence: 15, perception: 20 } },
              { id: 'ancient_knowledge', name: 'Ancient Knowledge', cost: 2, effect: { lore_master: 25, magic_bonus: 20 } },
              { id: 'prophecy_vision', name: 'Prophecy Vision', cost: 3, effect: { foresight: 30, danger_sense: 25 } },
              { id: 'time_wisdom', name: 'Time Wisdom', cost: 4, effect: { temporal_insight: 35, slow_time: 25 } },
              { id: 'cosmic_knowledge', name: 'Cosmic Knowledge', cost: 5, effect: { omniscience: 40, cosmic_power: 50 } }
            ]
          }
        }
      }
    };

    for (const [petType, tree] of Object.entries(skillTrees)) {
      this.skillTrees.set(petType, tree);
    }
  }

  initializeEvolutionRequirements() {
    const requirements = {
      // Base requirements that apply to all evolutions
      base: {
        level: { min: 1, scaling: true },
        bonding: { min: 20, scaling: true },
        experience: { min: 0, scaling: true }
      },

      // Special condition requirements
      special: {
        alpha_pack_trial: {
          description: 'Successfully lead a pack through a dangerous trial',
          check: (pet) => this.checkPackTrial(pet)
        },
        spirit_of_the_pack: {
          description: 'Achieve spiritual connection with the pack ancestors',
          check: (pet) => this.checkSpiritConnection(pet)
        },
        eternal_flame: {
          description: 'Absorb the eternal flame from the Sun Temple',
          check: (pet) => this.checkEternalFlame(pet)
        },
        dragon_ancestry: {
          description: 'Discover and embrace ancient dragon bloodline',
          check: (pet) => this.checkDragonAncestry(pet)
        },
        fairy_queen_blessing: {
          description: 'Receive blessing from the Fairy Queen',
          check: (pet) => this.checkFairyBlessing(pet)
        }
      }
    };

    for (const [key, req] of Object.entries(requirements)) {
      this.evolutionRequirements.set(key, req);
    }
  }

  initializeSpecialEvolutions() {
    const specialEvolutions = {
      // Environmental evolutions
      shadow_wolf_evolution: {
        from: 'wolf',
        condition: 'shadow_affinity',
        result: 'shadow_wolf_alpha',
        requirements: {
          shadow_crystals: 5,
          dark_ritual_complete: true,
          shadow_bonding: 80
        }
      },

      ice_phoenix_evolution: {
        from: 'phoenix',
        condition: 'ice_affinity',
        result: 'ice_phoenix',
        requirements: {
          frozen_heart: 1,
          winter_shrine_complete: true,
          ice_mastery: 70
        }
      },

      // Elemental evolutions
      elemental_dragon: {
        from: 'dragon_whelp',
        condition: 'elemental_purity',
        result: 'elemental_dragon_lord',
        requirements: {
          elemental_cores: 4,
          elemental_balance: true,
          dragon_elemental_trial: true
        }
      },

      // Divine evolutions
      celestial_wolf: {
        from: 'wolf',
        condition: 'divine_blessing',
        result: 'celestial_guardian_wolf',
        requirements: {
          divine_blessing_received: true,
          celestial_shrine_complete: true,
          heavenly_bond: 90
        }
      }
    };

    for (const [key, evolution] of Object.entries(specialEvolutions)) {
      this.specialEvolutions.set(key, evolution);
    }
  }

  // Main evolution methods
  checkEvolutionReadiness(pet) {
    const evolutionTree = this.evolutionTrees.get(pet.typeId);
    if (!evolutionTree) {
      return { ready: false, reason: 'no_evolution_path' };
    }

    const currentStage = evolutionTree.stages[pet.evolutionStage];
    if (!currentStage) {
      return { ready: false, reason: 'max_evolution_reached' };
    }

    // Check if already at max stage
    if (pet.evolutionStage >= evolutionTree.stages.length - 1) {
      return { ready: false, reason: 'max_evolution_reached' };
    }

    const nextStage = evolutionTree.stages[pet.evolutionStage + 1];
    const readiness = this.checkEvolutionRequirements(pet, nextStage);

    return {
      ready: readiness.allMet,
      requirements: readiness,
      nextStage: nextStage,
      currentProgress: readiness.progress
    };
  }

  checkEvolutionRequirements(pet, stage) {
    const requirements = stage.requirements;
    const checks = {
      level: this.checkLevelRequirement(pet, requirements.level),
      bonding: this.checkBondingRequirement(pet, requirements.bonding),
      experience: this.checkExperienceRequirement(pet, requirements.experience),
      skills: this.checkSkillRequirements(pet, requirements.skills),
      special: this.checkSpecialRequirements(pet, requirements.special)
    };

    const allMet = Object.values(checks).every(check => check.met);
    const progress = this.calculateEvolutionProgress(checks);

    return { allMet, progress, ...checks };
  }

  checkLevelRequirement(pet, requirement) {
    const requiredLevel = requirement || (pet.evolutionStage + 1) * 20;
    const met = pet.level >= requiredLevel;
    const progress = Math.min(1.0, pet.level / requiredLevel);

    return { met, required: requiredLevel, current: pet.level, progress };
  }

  checkBondingRequirement(pet, requirement) {
    const requiredBonding = requirement || (pet.evolutionStage + 1) * 20;
    const met = pet.bonding >= requiredBonding;
    const progress = Math.min(1.0, pet.bonding / requiredBonding);

    return { met, required: requiredBonding, current: pet.bonding, progress };
  }

  checkExperienceRequirement(pet, requirement) {
    const requiredExp = requirement || pet.calculateExperienceNeeded();
    const met = pet.experience >= requiredExp;
    const progress = Math.min(1.0, pet.experience / requiredExp);

    return { met, required: requiredExp, current: pet.experience, progress };
  }

  checkSkillRequirements(pet, requiredSkills) {
    if (!requiredSkills || requiredSkills.length === 0) {
      return { met: true, required: [], current: [], progress: 1.0 };
    }

    const currentSkills = pet.unlockedSkills || [];
    const missingSkills = requiredSkills.filter(skill => !currentSkills.includes(skill));
    const met = missingSkills.length === 0;
    const progress = (requiredSkills.length - missingSkills.length) / requiredSkills.length;

    return { met, required: requiredSkills, current: currentSkills, missing: missingSkills, progress };
  }

  checkSpecialRequirements(pet, specialRequirements) {
    if (!specialRequirements) {
      return { met: true, requirements: [], progress: 1.0 };
    }

    const specialReq = this.evolutionRequirements.get('special')?.[specialRequirements];
    if (!specialReq) {
      return { met: false, requirements: [specialRequirements], progress: 0 };
    }

    const met = specialReq.check(pet);
    const progress = met ? 1.0 : 0.0;

    return { met, requirements: [specialRequirements], description: specialReq.description, progress };
  }

  calculateEvolutionProgress(checks) {
    const weights = {
      level: 0.3,
      bonding: 0.25,
      experience: 0.2,
      skills: 0.15,
      special: 0.1
    };

    let totalProgress = 0;
    let totalWeight = 0;

    for (const [checkName, check] of Object.entries(checks)) {
      if (check.progress !== undefined) {
        totalProgress += check.progress * (weights[checkName] || 0.1);
        totalWeight += weights[checkName] || 0.1;
      }
    }

    return totalWeight > 0 ? totalProgress / totalWeight : 0;
  }

  async performEvolution(pet, forced = false) {
    const readiness = this.checkEvolutionReadiness(pet);

    if (!readiness.ready && !forced) {
      return { success: false, reason: 'requirements_not_met', details: readiness };
    }

    const evolutionTree = this.evolutionTrees.get(pet.typeId);
    const nextStage = evolutionTree.stages[pet.evolutionStage + 1];

    try {
      // Begin evolution process
      const evolutionResult = await this.executeEvolution(pet, nextStage);

      if (evolutionResult.success) {
        // Apply evolution changes
        await this.applyEvolutionChanges(pet, nextStage, evolutionResult);

        // Add evolution memory
        pet.addMemory({
          type: 'evolution',
          content: `Evolved to ${nextStage.name}`,
          importance: 5
        });

        return {
          success: true,
          previousStage: pet.evolutionStage,
          newStage: pet.evolutionStage,
          changes: evolutionResult.changes,
          evolutionName: nextStage.name
        };
      } else {
        return evolutionResult;
      }
    } catch (error) {
      return {
        success: false,
        reason: 'evolution_failed',
        error: error.message
      };
    }
  }

  async executeEvolution(pet, targetStage) {
    const evolutionDuration = this.calculateEvolutionDuration(pet, targetStage);

    // Evolution would typically be a timed process
    // For now, we'll simulate it as immediate
    const success = Math.random() < 0.95; // 95% success rate

    if (!success) {
      return {
        success: false,
        reason: 'evolution_failed_random',
        message: 'The evolution process failed due to unstable magical energies'
      };
    }

    const changes = this.generateEvolutionChanges(pet, targetStage);

    return {
      success: true,
      changes,
      duration: evolutionDuration
    };
  }

  calculateEvolutionDuration(pet, targetStage) {
    const baseDuration = 30000; // 30 seconds base
    const stageMultiplier = Math.pow(1.5, targetStage.level / 10);
    const bondingBonus = (pet.bonding / 100) * 0.3; // Better bonding = faster evolution

    return Math.floor(baseDuration * stageMultiplier * (1 - bondingBonus));
  }

  generateEvolutionChanges(pet, targetStage) {
    const changes = {
      statIncreases: {},
      newAbilities: [],
      traitChanges: [],
      visualChanges: targetStage.visualChanges || [],
      sizeIncrease: 0,
      skillPointsAwarded: 0
    };

    // Stat increases based on evolution stage
    const statMultipliers = {
      1: { health: 1.2, attack: 1.15, defense: 1.1, speed: 1.05, intelligence: 1.1 },
      2: { health: 1.4, attack: 1.3, defense: 1.25, speed: 1.15, intelligence: 1.2 },
      3: { health: 1.6, attack: 1.5, defense: 1.4, speed: 1.25, intelligence: 1.35 },
      4: { health: 1.8, attack: 1.7, defense: 1.6, speed: 1.35, intelligence: 1.5 },
      5: { health: 2.0, attack: 1.9, defense: 1.8, speed: 1.5, intelligence: 1.7 }
    };

    const multiplier = statMultipliers[pet.evolutionStage + 1] || statMultipliers[1];

    for (const [stat, value] of Object.entries(pet.stats)) {
      const increase = Math.floor(value * (multiplier[stat] - 1));
      if (increase > 0) {
        changes.statIncreases[stat] = increase;
      }
    }

    // New abilities based on evolution stage
    const stageAbilities = this.getStageAbilities(pet.typeId, pet.evolutionStage + 1);
    changes.newAbilities = stageAbilities;

    // Trait changes
    const newTraits = this.getEvolutionTraits(pet.typeId, pet.evolutionStage + 1);
    changes.traitChanges = newTraits;

    // Size increase
    changes.sizeIncrease = (pet.evolutionStage + 1) * 0.2; // 20% per stage

    // Skill points
    changes.skillPointsAwarded = pet.evolutionStage + 1;

    return changes;
  }

  getStageAbilities(petType, stage) {
    const abilityMap = {
      wolf: {
        1: ['enhanced_senses'],
        2: ['pack_howl', 'alpha_presence'],
        3: ['coordination_hunt', 'territorial_mark'],
        4: ['spirit_pack', 'ancient_howl'],
        5: ['alpha_command', 'legendary_pack']
      },
      phoenix: {
        1: ['fire_resistance'],
        2: ['heat_aura', 'ember_burst'],
        3: ['rebirth_flame', 'solar_wings'],
        4: ['phoenix_ashes', 'solar_healing'],
        5: ['immortal_flame', 'sun_divinity']
      },
      dragon_whelp: {
        1: ['dragon_scales'],
        2: ['wing_buffet', 'dragon_roar'],
        3: ['elemental_breath', 'dragon_intimidation'],
        4: ['flight_mastery', 'dragon_aura'],
        5: ['ancient_wisdom', 'dragon_lord']
      }
    };

    return abilityMap[petType]?.[stage] || [];
  }

  getEvolutionTraits(petType, stage) {
    const traitMap = {
      wolf: {
        1: ['enhanced'],
        2: ['alpha_potential'],
        3: ['pack_leader'],
        4: ['spirit_bonded'],
        5: ['legendary_alpha']
      },
      phoenix: {
        1: ['fire_blessed'],
        2: ['reborn'],
        3: ['solar_touched'],
        4: ['immortal_spark'],
        5: ['celestial_phoenix']
      },
      dragon_whelp: {
        1: ['dragon_blood'],
        2: ['winged'],
        3: ['elemental_attuned'],
        4: ['ancient_wisdom'],
        5: ['dragon_lord']
      }
    };

    return traitMap[petType]?.[stage] || [];
  }

  async applyEvolutionChanges(pet, targetStage, changes) {
    // Update evolution stage
    pet.evolutionStage++;
    pet.evolutionProgress = 0;

    // Apply stat increases
    for (const [stat, increase] of Object.entries(changes.statIncreases)) {
      pet.stats[stat] += increase;
      if (stat === 'health') {
        pet.maxHealth += increase;
        pet.currentHealth += increase;
      }
    }

    // Add new abilities
    pet.abilities.push(...changes.newAbilities);

    // Add new traits
    pet.traits.push(...changes.traitChanges);

    // Award skill points
    pet.skillPoints += changes.skillPointsAwarded;

    // Update visual representation
    pet.visualChanges = changes.visualChanges;
    pet.size = (pet.size || 1.0) + changes.sizeIncrease;

    // Evolution-specific effects
    await this.applyEvolutionSpecificEffects(pet, targetStage);
  }

  async applyEvolutionSpecificEffects(pet, stage) {
    // Apply special effects based on evolution stage and pet type
    switch (pet.typeId) {
      case 'wolf':
        if (pet.evolutionStage >= 3) {
          pet.traits.push('pack_summoner');
        }
        if (pet.evolutionStage >= 5) {
          pet.abilities.push('summon_spirit_pack');
        }
        break;

      case 'phoenix':
        if (pet.evolutionStage >= 3) {
          pet.traits.push('auto_rebirth');
        }
        if (pet.evolutionStage >= 5) {
          pet.abilities.push('solar_resurrection');
        }
        break;

      case 'dragon_whelp':
        if (pet.evolutionStage >= 2) {
          pet.traits.push('flight_capable');
        }
        if (pet.evolutionStage >= 4) {
          pet.abilities.push('dragon_landing');
        }
        break;
    }
  }

  // Skill tree methods
  getSkillTree(petType) {
    return this.skillTrees.get(petType) || null;
  }

  canUnlockSkill(pet, skillId, branchId) {
    const skillTree = this.getSkillTree(pet.typeId);
    if (!skillTree) return { canUnlock: false, reason: 'no_skill_tree' };

    const branch = skillTree.branches[branchId];
    if (!branch) return { canUnlock: false, reason: 'invalid_branch' };

    const skill = branch.skills.find(s => s.id === skillId);
    if (!skill) return { canUnlock: false, reason: 'skill_not_found' };

    // Check if pet has enough skill points
    if (pet.skillPoints < skill.cost) {
      return { canUnlock: false, reason: 'insufficient_points', required: skill.cost, current: pet.skillPoints };
    }

    // Check if prerequisites are met
    const skillIndex = branch.skills.findIndex(s => s.id === skillId);
    if (skillIndex > 0) {
      const previousSkill = branch.skills[skillIndex - 1];
      if (!pet.unlockedSkills.includes(previousSkill.id)) {
        return { canUnlock: false, reason: 'prerequisite_not_met', required: previousSkill.id };
      }
    }

    // Check if already unlocked
    if (pet.unlockedSkills.includes(skillId)) {
      return { canUnlock: false, reason: 'already_unlocked' };
    }

    return { canUnlock: true, skill, cost: skill.cost };
  }

  unlockSkill(pet, skillId, branchId) {
    const canUnlock = this.canUnlockSkill(pet, skillId, branchId);

    if (!canUnlock.canUnlock) {
      return { success: false, reason: canUnlock.reason };
    }

    // Deduct skill points
    pet.skillPoints -= canUnlock.cost;

    // Add skill to unlocked skills
    pet.unlockedSkills.push(skillId);

    // Apply skill effects
    this.applySkillEffects(pet, canUnlock.skill);

    // Add memory
    pet.addMemory({
      type: 'skill_learned',
      content: `Learned skill: ${canUnlock.skill.name}`,
      importance: 3
    });

    return {
      success: true,
      skill: canUnlock.skill,
      remainingPoints: pet.skillPoints
    };
  }

  applySkillEffects(pet, skill) {
    if (!skill.effect) return;

    for (const [effectName, value] of Object.entries(skill.effect)) {
      switch (effectName) {
        case 'leadership':
        case 'social_bonus':
        case 'intelligence':
        case 'perception':
          // These would affect various gameplay mechanics
          pet.skillEffects = pet.skillEffects || {};
          pet.skillEffects[effectName] = (pet.skillEffects[effectName] || 0) + value;
          break;

        case 'fire_defense':
        case 'burn_immunity':
          // Apply to damage calculations
          pet.resistances = pet.resistances || {};
          pet.resistances.fire = (pet.resistances.fire || 0) + value;
          break;

        default:
          // Generic stat effect
          pet.stats[effectName] = (pet.stats[effectName] || 0) + value;
          break;
      }
    }
  }

  // Special evolution methods
  checkSpecialEvolutionConditions(pet) {
    const possibleEvolutions = [];

    for (const [evolutionId, evolution] of this.specialEvolutions.entries()) {
      if (evolution.from === pet.typeId) {
        const conditionMet = this.checkSpecialCondition(pet, evolution.condition);
        const requirementsMet = this.checkSpecialEvolutionRequirements(pet, evolution.requirements);

        if (conditionMet && requirementsMet.met) {
          possibleEvolutions.push({
            id: evolutionId,
            name: evolution.result,
            description: `Evolve into ${evolution.result} through special means`,
            requirements: requirementsMet
          });
        }
      }
    }

    return possibleEvolutions;
  }

  checkSpecialCondition(pet, condition) {
    const conditionChecks = {
      shadow_affinity: () => pet.traits.includes('shadow_affinity') || pet.abilities.includes('shadow_blend'),
      ice_affinity: () => pet.traits.includes('ice_affinity') || pet.abilities.includes('frost_armor'),
      elemental_purity: () => pet.abilities.filter(a => a.includes('elemental')).length >= 2,
      divine_blessing: () => pet.traits.includes('divine_touched') || pet.abilities.includes('divine_light')
    };

    return conditionChecks[condition]?.() || false;
  }

  checkSpecialEvolutionRequirements(pet, requirements) {
    const checks = [];
    let allMet = true;

    for (const [reqName, reqValue] of Object.entries(requirements)) {
      let met = false;

      switch (reqName) {
        case 'shadow_crystals':
          met = this.checkInventoryItem(pet.ownerId, 'shadow_crystal', reqValue);
          break;
        case 'dark_ritual_complete':
          met = pet.eventFlags.dark_ritual_complete === true;
          break;
        case 'shadow_bonding':
          met = pet.bonding >= reqValue;
          break;
        case 'elemental_cores':
          met = this.checkElementalCores(pet, reqValue);
          break;
        case 'divine_blessing_received':
          met = pet.eventFlags.divine_blessing_received === true;
          break;
        default:
          met = pet[reqName] >= reqValue || pet.eventFlags[reqName] === reqValue;
          break;
      }

      checks.push({ requirement: reqName, met, required: reqValue });
      if (!met) allMet = false;
    }

    return { met: allMet, checks };
  }

  checkInventoryItem(playerId, itemId, quantity) {
    // This would check the player's inventory
    // For now, return true as placeholder
    return true;
  }

  checkElementalCores(pet, required) {
    const elementalTypes = ['fire', 'ice', 'earth', 'air'];
    const owned = elementalTypes.filter(type =>
      pet.abilities.includes(`${type}_core`) || pet.traits.includes(`${type}_attuned`)
    ).length;
    return owned >= required;
  }

  async performSpecialEvolution(pet, evolutionId) {
    const evolution = this.specialEvolutions.get(evolutionId);
    if (!evolution) {
      return { success: false, reason: 'invalid_evolution' };
    }

    if (evolution.from !== pet.typeId) {
      return { success: false, reason: 'incompatible_pet_type' };
    }

    // Check conditions again
    const conditionMet = this.checkSpecialCondition(pet, evolution.condition);
    const requirementsMet = this.checkSpecialEvolutionRequirements(pet, evolution.requirements);

    if (!conditionMet || !requirementsMet.met) {
      return { success: false, reason: 'conditions_not_met', details: requirementsMet };
    }

    try {
      // Perform special evolution
      const result = await this.executeSpecialEvolution(pet, evolution);

      if (result.success) {
        // Update pet type
        pet.typeId = evolution.result;

        // Reset evolution stage for new type
        pet.evolutionStage = 0;

        // Add special evolution trait
        pet.traits.push('special_evolution');
        pet.traits.push(`${evolutionId}_evolved`);

        // Add memory
        pet.addMemory({
          type: 'special_evolution',
          content: `Underwent special evolution into ${evolution.result}`,
          importance: 5
        });

        return {
          success: true,
          previousType: evolution.from,
          newType: evolution.result,
          changes: result.changes
        };
      } else {
        return result;
      }
    } catch (error) {
      return {
        success: false,
        reason: 'special_evolution_failed',
        error: error.message
      };
    }
  }

  async executeSpecialEvolution(pet, evolution) {
    // Special evolution might have unique requirements and effects
    const changes = {
      statIncreases: this.generateSpecialEvolutionStats(pet, evolution),
      newAbilities: this.getSpecialEvolutionAbilities(evolution),
      traitChanges: this.getSpecialEvolutionTraits(evolution),
      visualChanges: ['special_evolution_aura'],
      uniqueEffects: this.getSpecialEvolutionEffects(evolution)
    };

    return {
      success: true,
      changes
    };
  }

  generateSpecialEvolutionStats(pet, evolution) {
    // Special evolutions provide better stat increases
    const statIncrease = {
      health: 50,
      attack: 30,
      defense: 40,
      speed: 20,
      intelligence: 35
    };

    // Adjust based on evolution type
    if (evolution.result.includes('shadow')) {
      statIncrease.speed += 15;
      statIncrease.intelligence += 10;
    }
    if (evolution.result.includes('ice')) {
      statIncrease.defense += 20;
      statIncrease.health += 30;
    }
    if (evolution.result.includes('celestial')) {
      statIncrease.intelligence += 25;
      statIncrease.health += 40;
    }

    return statIncrease;
  }

  getSpecialEvolutionAbilities(evolution) {
    const abilityMap = {
      shadow_wolf_alpha: ['shadow_step', 'dark_howl', 'night_vision_enhanced'],
      ice_phoenix: ['ice_rebirth', 'blizzard_wings', 'frost_healing'],
      elemental_dragon_lord: ['elemental_mastery', 'dragon_elements', 'elemental_aura'],
      celestial_guardian_wolf: ['divine_protection', 'holy_howl', 'celestial_pack']
    };

    return abilityMap[evolution.result] || [];
  }

  getSpecialEvolutionTraits(evolution) {
    const traitMap = {
      shadow_wolf_alpha: ['shadow_master', 'night_lord', 'alpha_shadow'],
      ice_phoenix: ['ice_immortal', 'winter_spirit', 'frost_reborn'],
      elemental_dragon_lord: ['elemental_god', 'dragon_elemental', 'primordial'],
      celestial_guardian_wolf: ['celestial_guardian', 'holy_protector', 'divine_alpha']
    };

    return traitMap[evolution.result] || [];
  }

  getSpecialEvolutionEffects(evolution) {
    const effectMap = {
      shadow_wolf_alpha: ['shadow_aura', 'night_vision_supreme', 'shadow_pack_summon'],
      ice_phoenix: ['ice_aura', 'winter_domain', 'absolute_zero'],
      elemental_dragon_lord: ['elemental_control', 'dragon_elements_supreme', 'primordial_power'],
      celestial_guardian_wolf: ['divine_aura', 'holy_protection', 'celestial_pack_summon']
    };

    return effectMap[evolution.result] || [];
  }

  // Special requirement checks
  checkPackTrial(pet) {
    // Check if pet has completed pack trial
    return pet.eventFlags.pack_trial_completed === true;
  }

  checkSpiritConnection(pet) {
    // Check spiritual connection with pack ancestors
    return pet.traits.includes('spirit_touched') && pet.bonding >= 90;
  }

  checkEternalFlame(pet) {
    // Check if pet has absorbed eternal flame
    return pet.abilities.includes('eternal_flame_absorbed');
  }

  checkDragonAncestry(pet) {
    // Check dragon bloodline discovery
    return pet.traits.includes('ancient_dragon_blood') && pet.level >= 80;
  }

  checkFairyBlessing(pet) {
    // Check fairy queen blessing
    return pet.eventFlags.fairy_queen_blessing === true && pet.traits.includes('fairy_blessed');
  }
}

module.exports = EvolutionSystem;