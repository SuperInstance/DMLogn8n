/**
 * Character Features Automation System
 * Handles class features, racial traits, feats, and multiclassing
 */

import { ABILITIES, SKILLS } from '../types/index.js';

export class CharacterFeatures {
  constructor() {
    this.classFeatures = new Map(); // className -> features
    this.racialTraits = new Map(); // raceName -> traits
    this.featDatabase = new Map(); // featName -> feat data
    this.multiclassRules = new Map(); // class -> multiclass rules
    this.initializeFeatureData();
  }

  /**
   * Initialize all feature data
   */
  initializeFeatureData() {
    this.initializeClassFeatures();
    this.initializeRacialTraits();
    this.initializeFeats();
    this.initializeMulticlassRules();
  }

  /**
   * Initialize class features
   */
  initializeClassFeatures() {
    // Fighter Features
    this.classFeatures.set('fighter', {
      1: [
        {
          name: 'Fighting Style',
          type: 'feature',
          description: 'Choose a fighting style',
          choices: ['Archery', 'Defense', 'Dueling', 'Great Weapon Fighting', 'Protection', 'Two-Weapon Fighting'],
          effect: (character, choice) => this.applyFightingStyle(character, choice)
        },
        {
          name: 'Second Wind',
          type: 'action',
          description: 'Regain hit points as a bonus action',
          uses: 'shortRest',
          effect: (character) => this.applySecondWind(character)
        }
      ],
      2: [
        {
          name: 'Action Surge',
          type: 'action',
          description: 'Take an additional action on your turn',
          uses: 'shortRest',
          effect: (character) => { character.bonusAction = true; }
        }
      ],
      3: [
        {
          name: 'Martial Archetype',
          type: 'subclass',
          description: 'Choose a martial archetype',
          choices: ['Battle Master', 'Champion', 'Eldritch Knight', 'Psi Warrior', 'Rune Knight', 'Samurai']
        }
      ],
      4: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      5: [
        {
          name: 'Extra Attack',
          type: 'passive',
          description: 'Attack twice whenever you take the Attack action',
          effect: (character) => { character.extraAttacks = 1; }
        }
      ],
      6: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      7: [
        {
          name: 'Martial Archetype Feature',
          type: 'subclass',
          description: 'Gain archetype feature'
        }
      ],
      8: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      9: [
        {
          name: 'Indomitable',
          type: 'feature',
          description: 'Reroll a failed saving throw',
          uses: 'longRest',
          effect: (character) => { character.hasIndomitable = true; }
        }
      ],
      10: [
        {
          name: 'Martial Archetype Feature',
          type: 'subclass',
          description: 'Gain archetype feature'
        }
      ]
    });

    // Rogue Features
    this.classFeatures.set('rogue', {
      1: [
        {
          name: 'Expertise',
          type: 'feature',
          description: 'Choose two skills or one skill and thieves\' tools to double proficiency bonus',
          effect: (character, choices) => this.applyExpertise(character, choices)
        },
        {
          name: 'Sneak Attack',
          type: 'passive',
          description: 'Deal extra damage when attacking with advantage or against target next to ally',
          effect: (character) => { character.sneakAttack = this.calculateSneakAttack(character.level); }
        },
        {
          name: 'Thieves\' Cant',
          type: 'language',
          description: 'Learn secret thieves\' language'
        }
      ],
      2: [
        {
          name: 'Cunning Action',
          type: 'bonus_action',
          description: 'Dash, Disengage, or Hide as bonus action',
          effect: (character) => { character.hasCunningAction = true; }
        }
      ],
      3: [
        {
          name: 'Roguish Archetype',
          type: 'subclass',
          description: 'Choose a roguish archetype',
          choices: ['Thief', 'Assassin', 'Arcane Trickster', 'Inquisitive', 'Mastermind', 'Scout', 'Soulknife', 'Swashbuckler']
        }
      ],
      4: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      5: [
        {
          name: 'Uncanny Dodge',
          type: 'reaction',
          description: 'Half damage from attack when you can see attacker',
          effect: (character) => { character.hasUncannyDodge = true; }
        }
      ],
      6: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      7: [
        {
          name: 'Evasion',
          type: 'passive',
          description: 'No damage on successful Dexterity saves, half damage on failed saves',
          effect: (character) => { character.hasEvasion = true; }
        }
      ],
      8: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      9: [
        {
          name: 'Roguish Archetype Feature',
          type: 'subclass',
          description: 'Gain archetype feature'
        }
      ],
      10: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ]
    });

    // Wizard Features
    this.classFeatures.set('wizard', {
      1: [
        {
          name: 'Spellcasting',
          type: 'feature',
          description: 'Learn and cast spells',
          effect: (character) => this.initializeSpellcasting(character, 'wizard', 'intelligence')
        },
        {
          name: 'Arcane Recovery',
          type: 'feature',
          description: 'Recover spell slots during short rest',
          uses: 'oncePerDay',
          effect: (character) => { character.hasArcaneRecovery = true; }
        }
      ],
      2: [
        {
          name: 'Arcane Tradition',
          type: 'subclass',
          description: 'Choose an arcane tradition',
          choices: ['Abjuration', 'Conjuration', 'Divination', 'Enchantment', 'Evocation', 'Illusion', 'Necromancy', 'Transmutation']
        }
      ],
      3: [
        {
          name: '2nd Level Spells',
          type: 'feature',
          description: 'Access to 2nd level spells'
        }
      ],
      4: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      5: [
        {
          name: '3rd Level Spells',
          type: 'feature',
          description: 'Access to 3rd level spells'
        }
      ],
      6: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      7: [
        {
          name: '4th Level Spells',
          type: 'feature',
          description: 'Access to 4th level spells'
        }
      ],
      8: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      9: [
        {
          name: '5th Level Spells',
          type: 'feature',
          description: 'Access to 5th level spells'
        }
      ],
      10: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ]
    });

    // Cleric Features
    this.classFeatures.set('cleric', {
      1: [
        {
          name: 'Spellcasting',
          type: 'feature',
          description: 'Learn and cast spells',
          effect: (character) => this.initializeSpellcasting(character, 'cleric', 'wisdom')
        },
        {
          name: 'Divine Domain',
          type: 'subclass',
          description: 'Choose a divine domain',
          choices: ['Knowledge', 'Life', 'Light', 'Nature', 'Tempest', 'Trickery', 'War', 'Forge', 'Grave', 'Order', 'Peace', 'Twilight']
        }
      ],
      2: [
        {
          name: 'Channel Divinity (1/rest)',
          type: 'feature',
          description: 'Channel divine energy',
          uses: 'shortRest'
        }
      ],
      3: [
        {
          name: '2nd Level Spells',
          type: 'feature',
          description: 'Access to 2nd level spells'
        }
      ],
      4: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      5: [
        {
          name: 'Destroy Undead (CR 1/2)',
          type: 'feature',
          description: 'Destroy lower-CR undead'
        }
      ],
      6: [
        {
          name: 'Channel Divinity (2/rest)',
          type: 'feature',
          description: 'Use Channel Divinity twice per rest'
        },
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        }
      ],
      7: [
        {
          name: '4th Level Spells',
          type: 'feature',
          description: 'Access to 4th level spells'
        }
      ],
      8: [
        {
          name: 'Ability Score Improvement',
          type: 'asi',
          description: 'Increase ability scores or take a feat'
        },
        {
          name: 'Destroy Undead (CR 1)',
          type: 'feature',
          description: 'Destroy higher-CR undead'
        }
      ],
      9: [
        {
          name: '5th Level Spells',
          type: 'feature',
          description: 'Access to 5th level spells'
        }
      ],
      10: [
        {
          name: 'Divine Intervention',
          type: 'feature',
          description: 'Request divine aid',
          uses: 'oncePerDay'
        }
      ]
    });
  }

  /**
   * Initialize racial traits
   */
  initializeRacialTraits() {
    this.racialTraits.set('human', {
      name: 'Human',
      abilityScoreIncrease: { all: 1 },
      traits: [
        {
          name: 'Variant Human Traits',
          description: 'Choose two different ability scores to increase',
          type: 'choice',
          choices: Object.values(ABILITIES),
          select: 2
        },
        {
          name: 'Skill Proficiency',
          description: 'Gain one skill proficiency',
          type: 'choice',
          choices: Object.values(SKILLS),
          select: 1
        },
        {
          name: 'Feat',
          description: 'Gain one feat',
          type: 'choice',
          choices: 'anyFeat',
          select: 1
        }
      ]
    });

    this.racialTraits.set('elf', {
      name: 'Elf',
      abilityScoreIncrease: { dexterity: 2 },
      traits: [
        {
          name: 'Fey Ancestry',
          description: 'Advantage on saves against being charmed, magic can\'t put you to sleep',
          type: 'passive'
        },
        {
          name: 'Trance',
          description: 'Meditate for 4 hours instead of sleeping for 8',
          type: 'passive'
        },
        {
          name: 'Keen Senses',
          description: 'Perception proficiency',
          type: 'proficiency',
          skill: SKILLS.PERCEPTION
        }
      ]
    });

    this.racialTraits.set('dwarf', {
      name: 'Dwarf',
      abilityScoreIncrease: { constitution: 2 },
      traits: [
        {
          name: 'Dwarven Resilience',
          description: 'Advantage on poison saves, resistance to poison damage',
          type: 'resistance',
          damageType: 'poison'
        },
        {
          name: 'Dwarven Combat Training',
          description: 'Proficiency with battleaxe, handaxe, light hammer, warhammer',
          type: 'weapon_proficiency',
          weapons: ['battleaxe', 'handaxe', 'light hammer', 'warhammer']
        },
        {
          name: 'Stonecunning',
          description: 'Double proficiency bonus on Intelligence (History) checks about stonework',
          type: 'expertise',
          skill: 'history_stonework'
        }
      ]
    });

    this.racialTraits.set('halfling', {
      name: 'Halfling',
      abilityScoreIncrease: { dexterity: 2 },
      traits: [
        {
          name: 'Lucky',
          description: 'Reroll 1s on attack rolls, ability checks, and saving throws',
          type: 'passive'
        },
        {
          name: 'Brave',
          description: 'Advantage on saves against being frightened',
          type: 'passive'
        },
        {
          name: 'Halfling Nimbleness',
          description: 'Can move through space of creature larger than you',
          type: 'movement'
        }
      ]
    });
  }

  /**
   * Initialize feats
   */
  initializeFeats() {
    this.featDatabase.set('great_weapon_master', {
      name: 'Great Weapon Master',
      description: 'Heavy weapon mastery',
      prerequisites: [],
      benefits: [
        'On hit, bonus action attack with -5 penalty',
        '+10 damage when scoring critical hit or reducing creature to 0 HP'
      ],
      effect: (character) => {
        character.featGreatWeaponMaster = true;
      }
    });

    this.featDatabase.set('sharpshooter', {
      name: 'Sharpshooter',
      description: 'Ranged weapon mastery',
      prerequisites: [],
      benefits: [
        'Ignore cover and long range penalties',
        'On hit, bonus action attack with -5 penalty',
        '+10 damage when scoring critical hit or reducing creature to 0 HP'
      ],
      effect: (character) => {
        character.featSharpshooter = true;
      }
    });

    this.featDatabase.set('polearm_master', {
      name: 'Polearm Master',
      description: 'Polearm and spear mastery',
      prerequisites: [],
      benefits: [
        'Bonus action attack with other end of polearm',
        'Opportunity attack when creature enters reach',
        '+1 Strength or Dexterity'
      ],
      effect: (character, abilityIncrease) => {
        character.featPolearmMaster = true;
        if (abilityIncrease) {
          character.abilities[abilityIncrease] += 1;
        }
      }
    });

    this.featDatabase.set('war_caster', {
      name: 'War Caster',
      description: 'Spellcasting in combat',
      prerequisites: [],
      benefits: [
        'Advantage on Constitution saves to maintain concentration',
        'Perform somatic components with weapons/shields equipped',
        'Cast spells as opportunity attacks'
      ],
      effect: (character) => {
        character.featWarCaster = true;
      }
    });

    this.featDatabase.set('resilient', {
      name: 'Resilient',
      description: 'Choose one ability to gain proficiency in saving throws',
      prerequisites: [],
      benefits: [
        '+1 ability score',
        'Proficiency in saves with chosen ability'
      ],
      effect: (character, ability) => {
        character.abilities[ability] += 1;
        if (!character.savingThrowProficiencies) {
          character.savingThrowProficiencies = [];
        }
        character.savingThrowProficiencies.push(ability);
      }
    });

    this.featDatabase.set('sentinel', {
      name: 'Sentinel',
      description: 'Defensive combat specialist',
      prerequisites: [],
      benefits: [
        'Opportunity attacks don\'t consume reactions against creatures with 5+ speed',
        'Creature hit by opportunity attack has speed reduced to 0',
        'Creatures within 5 feet have disadvantage on attacks against targets other than you'
      ],
      effect: (character) => {
        character.featSentinel = true;
      }
    });

    this.featDatabase.set('mobile', {
      name: 'Mobile',
      description: 'Enhanced movement',
      prerequisites: [],
      benefits: [
        '+10 speed',
        'No opportunity attacks when using Dash action',
        'Difficult terrain doesn\'t slow movement'
      ],
      effect: (character) => {
        character.speed += 10;
        character.featMobile = true;
      }
    });

    this.featDatabase.set('tough', {
      name: 'Tough',
      description: 'Increased hit points',
      prerequisites: [],
      benefits: [
        '+2 hit points per level'
      ],
      effect: (character) => {
        const hpIncrease = character.level * 2;
        character.hitPoints.maximum += hpIncrease;
        character.hitPoints.current += hpIncrease;
      }
    });

    this.featDatabase.set('skill_expert', {
      name: 'Skill Expert',
      description: 'Master of one skill',
      prerequisites: [],
      benefits: [
        '+1 ability score',
        'Skill proficiency',
        'Expertise in chosen skill'
      ],
      effect: (character, ability, skill) => {
        character.abilities[ability] += 1;
        if (!character.skills[skill]) {
          character.skills[skill] = { proficient: true };
        }
        character.skills[skill].expertise = true;
      }
    });

    this.featDatabase.set('observant', {
      name: 'Observant',
      description: 'Perceptive and aware',
      prerequisites: [],
      benefits: [
        '+1 Wisdom or Intelligence',
        '+1 passive Perception and Investigation',
        'Read lips'
      ],
      effect: (character, ability) => {
        character.abilities[ability] += 1;
        character.passivePerceptionBonus = 1;
        character.passiveInvestigationBonus = 1;
        character.canReadLips = true;
      }
    });
  }

  /**
   * Initialize multiclass rules
   */
  initializeMulticlassRules() {
    this.multiclassRules.set('fighter', {
      requirements: { strength: 13, dexterity: 13 },
      proficienciesGained: ['all armor', 'shields', 'simple weapons', 'martial weapons'],
      featuresFromLevels: (levels) => {
        const features = [];
        if (levels >= 1) features.push('fighting style', 'second wind');
        if (levels >= 2) features.push('action surge');
        if (levels >= 3) features.push('martial archetype');
        if (levels >= 5) features.push('extra attack');
        return features;
      }
    });

    this.multiclassRules.set('rogue', {
      requirements: { dexterity: 13 },
      proficienciesGained: ['light armor', 'simple weapons', 'thieves tools'],
      featuresFromLevels: (levels) => {
        const features = [];
        if (levels >= 1) features.push('expertise', 'sneak attack', 'thieves cant');
        if (levels >= 2) features.push('cunning action');
        if (levels >= 3) features.push('roguish archetype');
        if (levels >= 5) features.push('uncanny dodge');
        return features;
      }
    });

    this.multiclassRules.set('wizard', {
      requirements: { intelligence: 13 },
      proficienciesGained: [],
      featuresFromLevels: (levels) => {
        const features = [];
        if (levels >= 1) features.push('spellcasting', 'arcane recovery');
        if (levels >= 2) features.push('arcane tradition');
        return features;
      }
    });

    this.multiclassRules.set('cleric', {
      requirements: { wisdom: 13 },
      proficienciesGained: ['light armor', 'medium armor', 'shields', 'simple weapons'],
      featuresFromLevels: (levels) => {
        const features = [];
        if (levels >= 1) features.push('spellcasting', 'divine domain');
        if (levels >= 2) features.push('channel divinity');
        return features;
      }
    });
  }

  /**
   * Apply class features to character
   * @param {Character} character - Character to modify
   * @param {string} className - Class name
   * @param {number} level - Class level
   * @param {object} choices - Character choices
   */
  applyClassFeatures(character, className, level, choices = {}) {
    const classFeatureMap = this.classFeatures.get(className);
    if (!classFeatureMap) {
      throw new Error(`Unknown class: ${className}`);
    }

    for (let currentLevel = 1; currentLevel <= level; currentLevel++) {
      const features = classFeatureMap[currentLevel] || [];
      features.forEach(feature => {
        this.applyFeature(character, feature, choices);
      });
    }
  }

  /**
   * Apply racial traits to character
   * @param {Character} character - Character to modify
   * @param {string} race - Character race
   * @param {object} choices - Racial choices
   */
  applyRacialTraits(character, race, choices = {}) {
    const racialData = this.racialTraits.get(race);
    if (!racialData) {
      throw new Error(`Unknown race: ${race}`);
    }

    // Apply ability score increases
    if (racialData.abilityScoreIncrease) {
      Object.entries(racialData.abilityScoreIncrease).forEach(([ability, amount]) => {
        if (ability === 'all') {
          Object.values(ABILITIES).forEach(ab => {
            character.abilities[ab] = (character.abilities[ab] || 10) + amount;
          });
        } else {
          character.abilities[ability] = (character.abilities[ability] || 10) + amount;
        }
      });
    }

    // Apply traits
    racialData.traits.forEach(trait => {
      this.applyTrait(character, trait, choices);
    });
  }

  /**
   * Apply feat to character
   * @param {Character} character - Character to modify
   * @param {string} featName - Feat name
   * @param {object} choices - Feat choices
   */
  applyFeat(character, featName, choices = {}) {
    const feat = this.featDatabase.get(featName);
    if (!feat) {
      throw new Error(`Unknown feat: ${featName}`);
    }

    // Check prerequisites
    if (!this.checkFeatPrerequisites(character, feat)) {
      throw new Error(`Character does not meet prerequisites for ${featName}`);
    }

    // Apply feat effect
    if (feat.effect) {
      feat.effect(character, choices.abilityIncrease, choices.skill, choices);
    }

    // Add to character's feat list
    if (!character.feats) character.feats = [];
    character.feats.push(featName);
  }

  /**
   * Handle multiclassing for character
   * @param {Character} character - Character to modify
   * @param {Array} classes - Array of class objects {class, level}
   */
  applyMulticlassing(character, classes) {
    if (classes.length === 1) {
      // Single class
      this.applyClassFeatures(character, classes[0].class, classes[0].level);
      return;
    }

    // Multiclassing
    classes.forEach(({ class: className, level }) => {
      // Check multiclass requirements
      const multiclassRule = this.multiclassRules.get(className);
      if (multiclassRule) {
        this.checkMulticlassRequirements(character, multiclassRule);
      }

      // Apply features from this class
      this.applyClassFeatures(character, className, level);
    });

    // Calculate multiclass spellcasting (if applicable)
    this.calculateMulticlassSpellcasting(character, classes);
  }

  /**
   * Apply a single feature to character
   * @param {Character} character - Character to modify
   * @param {object} feature - Feature to apply
   * @param {object} choices - Character choices
   */
  applyFeature(character, feature, choices) {
    if (!character.features) character.features = [];

    // Add feature to character's feature list
    character.features.push(feature);

    // Apply feature effect if present
    if (feature.effect) {
      const choice = choices[feature.name];
      feature.effect(character, choice);
    }

    // Handle special feature types
    switch (feature.type) {
      case 'subclass':
        // Handle subclass features (would need more detailed implementation)
        break;
      case 'asi':
        // Handle ability score improvement
        this.handleAbilityScoreImprovement(character, choices);
        break;
    }
  }

  /**
   * Apply a single trait to character
   * @param {Character} character - Character to modify
   * @param {object} trait - Trait to apply
   * @param {object} choices - Character choices
   */
  applyTrait(character, trait, choices) {
    if (!character.traits) character.traits = [];
    character.traits.push(trait);

    switch (trait.type) {
      case 'proficiency':
        if (trait.skill) {
          if (!character.skills) character.skills = {};
          character.skills[trait.skill] = { proficient: true };
        }
        break;
      case 'expertise':
        if (trait.skill) {
          if (!character.skills) character.skills = {};
          character.skills[trait.skill] = { proficient: true, expertise: true };
        }
        break;
      case 'resistance':
        if (!character.resistances) character.resistances = [];
        character.resistances.push(trait.damageType);
        break;
      case 'weapon_proficiency':
        if (!character.weaponProficiencies) character.weaponProficiencies = [];
        character.weaponProficiencies.push(...trait.weapons);
        break;
    }
  }

  /**
   * Apply fighting style to character
   * @param {Character} character - Character to modify
   * @param {string} style - Fighting style choice
   */
  applyFightingStyle(character, style) {
    switch (style) {
      case 'Archery':
        character.fightingStyle = 'archery';
        character.rangedAttackBonus = 2;
        break;
      case 'Defense':
        character.fightingStyle = 'defense';
        character.armorClassBonus = 1;
        break;
      case 'Dueling':
        character.fightingStyle = 'dueling';
        character.duelingDamageBonus = 2;
        break;
      case 'Great Weapon Fighting':
        character.fightingStyle = 'great_weapon';
        character.greatWeaponReroll = true;
        break;
      case 'Protection':
        character.fightingStyle = 'protection';
        character.protectionReaction = true;
        break;
      case 'Two-Weapon Fighting':
        character.fightingStyle = 'two_weapon';
        character.twoWeaponFightingBonus = true;
        break;
    }
  }

  /**
   * Apply expertise to character skills
   * @param {Character} character - Character to modify
   * @param {Array} choices - Skill/Tool choices
   */
  applyExpertise(character, choices) {
    if (!choices || choices.length === 0) return;

    choices.forEach(choice => {
      if (choice.includes('tool')) {
        // Tool expertise
        if (!character.toolExpertise) character.toolExpertise = [];
        character.toolExpertise.push(choice);
      } else {
        // Skill expertise
        if (!character.skills) character.skills = {};
        character.skills[choice] = { proficient: true, expertise: true };
      }
    });
  }

  /**
   * Calculate sneak attack damage
   * @param {number} level - Character level
   * @returns {string} Sneak attack dice
   */
  calculateSneakAttack(level) {
    const dice = Math.ceil(level / 2);
    return `${dice}d6`;
  }

  /**
   * Apply second wind to character
   * @param {Character} character - Character to heal
   */
  applySecondWind(character) {
    const healAmount = 10 + character.level;
    character.heal(healAmount);
    return {
      healed: healAmount,
      newHP: character.hitPoints.current
    };
  }

  /**
   * Initialize spellcasting for character
   * @param {Character} character - Character to modify
   * @param {string} className - Character class
   * @param {string} ability - Spellcasting ability
   */
  initializeSpellcasting(character, className, ability) {
    character.spellcasting = {
      class: className,
      ability: ability,
      spellAttackBonus: character.getAbilityModifier(ability) + character.proficiencyBonus,
      spellSaveDC: 8 + character.getAbilityModifier(ability) + character.proficiencyBonus
    };
  }

  /**
   * Check feat prerequisites
   * @param {Character} character - Character to check
   * @param {object} feat - Feat to check
   * @returns {boolean} Whether prerequisites are met
   */
  checkFeatPrerequisites(character, feat) {
    if (!feat.prerequisites || feat.prerequisites.length === 0) {
      return true;
    }

    return feat.prerequisites.every(prereq => {
      if (typeof prereq === 'string') {
        // Skill proficiency prerequisite
        return character.skills?.[prereq]?.proficient || false;
      } else if (typeof prereq === 'object') {
        // Ability score prerequisite
        return Object.entries(prereq).every(([ability, score]) =>
          (character.abilities[ability] || 10) >= score
        );
      }
      return false;
    });
  }

  /**
   * Check multiclass requirements
   * @param {Character} character - Character to check
   * @param {object} multiclassRule - Multiclass rules
   */
  checkMulticlassRequirements(character, multiclassRule) {
    if (!multiclassRule.requirements) return;

    const meetsRequirements = Object.entries(multiclassRule.requirements).every(
      ([ability, score]) => (character.abilities[ability] || 10) >= score
    );

    if (!meetsRequirements) {
      throw new Error(`Character does not meet multiclass requirements`);
    }
  }

  /**
   * Calculate multiclass spellcasting
   * @param {Character} character - Character to modify
   * @param {Array} classes - Character classes
   */
  calculateMulticlassSpellcasting(character, classes) {
    const spellcastingClasses = classes.filter(c =>
      ['wizard', 'sorcerer', 'warlock', 'bard', 'cleric', 'druid', 'paladin', 'ranger'].includes(c.class)
    );

    if (spellcastingClasses.length === 0) return;

    // Calculate multiclass spell slot levels (simplified)
    const totalLevels = spellcastingClasses.reduce((sum, c) => sum + c.level, 0);
    // This would use the official multiclass spellcaster table in full implementation
  }

  /**
   * Handle ability score improvement
   * @param {Character} character - Character to modify
   * @param {object} choices - ASI choices
   */
  handleAbilityScoreImprovement(character, choices) {
    if (choices.feat) {
      this.applyFeat(character, choices.feat, choices);
    } else if (choices.abilityIncreases) {
      choices.abilityIncreases.forEach(({ ability, amount }) => {
        character.abilities[ability] = (character.abilities[ability] || 10) + amount;
      });
    }
  }

  /**
   * Get available features for character
   * @param {Character} character - Character to check
   * @returns {Array} Available features
   */
  getAvailableFeatures(character) {
    const features = [];

    // Get class features
    if (character.class) {
      const classFeatures = this.classFeatures.get(character.class);
      if (classFeatures) {
        for (let level = 1; level <= character.level; level++) {
          const levelFeatures = classFeatures[level] || [];
          features.push(...levelFeatures);
        }
      }
    }

    // Get racial traits
    if (character.race) {
      const racialData = this.racialTraits.get(character.race);
      if (racialData && racialData.traits) {
        features.push(...racialData.traits);
      }
    }

    // Get feats
    if (character.feats) {
      character.feats.forEach(featName => {
        const feat = this.featDatabase.get(featName);
        if (feat) {
          features.push(feat);
        }
      });
    }

    return features;
  }
}

export default CharacterFeatures;