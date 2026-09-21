/**
 * Skill Checks System
 */

import { SKILLS, ABILITIES } from '../types/index.js';
import { DiceRoller } from '../core/DiceRoller.js';
import { AbilityChecks } from './AbilityChecks.js';

export class SkillChecks {
  /**
   * Skill to ability mapping
   */
  static SKILL_ABILITIES = {
    [SKILLS.ATHLETICS]: ABILITIES.STRENGTH,
    [SKILLS.ACROBATICS]: ABILITIES.DEXTERITY,
    [SKILLS.SLEIGHT_OF_HAND]: ABILITIES.DEXTERITY,
    [SKILLS.STEALTH]: ABILITIES.DEXTERITY,
    [SKILLS.ARCANA]: ABILITIES.INTELLIGENCE,
    [SKILLS.HISTORY]: ABILITIES.INTELLIGENCE,
    [SKILLS.INVESTIGATION]: ABILITIES.INTELLIGENCE,
    [SKILLS.NATURE]: ABILITIES.INTELLIGENCE,
    [SKILLS.RELIGION]: ABILITIES.INTELLIGENCE,
    [SKILLS.ANIMAL_HANDLING]: ABILITIES.WISDOM,
    [SKILLS.INSIGHT]: ABILITIES.WISDOM,
    [SKILLS.MEDICINE]: ABILITIES.WISDOM,
    [SKILLS.PERCEPTION]: ABILITIES.WISDOM,
    [SKILLS.SURVIVAL]: ABILITIES.WISDOM,
    [SKILLS.DECEPTION]: ABILITIES.CHARISMA,
    [SKILLS.INTIMIDATION]: ABILITIES.CHARISMA,
    [SKILLS.PERFORMANCE]: ABILITIES.CHARISMA,
    [SKILLS.PERSUASION]: ABILITIES.CHARISMA
  };

  /**
   * Perform a skill check
   * @param {Character} character - Character making the check
   * @param {string} skill - Skill to check
   * @param {number} dc - Difficulty class
   * @param {object} options - Additional options
   * @returns {object} Skill check result
   */
  static performCheck(character, skill, dc, options = {}) {
    const {
      advantage = 0,
      bonus = 0,
      passive = false,
      reliableTalent = false,
      jackOfAllTrades = false
    } = options;

    // Validate skill
    if (!Object.values(SKILLS).includes(skill)) {
      throw new Error(`Invalid skill: ${skill}`);
    }

    const ability = this.SKILL_ABILITIES[skill];
    const abilityModifier = character.getAbilityModifier(ability);
    const skillBonus = character.getSkillBonus(skill);
    let totalBonus = skillBonus + bonus;

    // Apply jack of all trades (half proficiency on unskilled checks)
    if (jackOfAllTrades && !character.skills?.[skill]?.proficient) {
      totalBonus += Math.floor(character.proficiencyBonus / 2);
    }

    if (passive) {
      // Passive skill check (10 + bonus)
      const passiveTotal = 10 + totalBonus;
      return {
        type: 'passive_skill_check',
        character: character.name,
        skill,
        ability,
        dc,
        total: passiveTotal,
        success: passiveTotal >= dc,
        bonus: totalBonus,
        passive: true
      };
    }

    // Active skill check
    const roll = DiceRoller.rollD20(advantage);

    // Apply reliable talent (treat rolls below 10 as 10)
    let adjustedRoll = roll.total;
    if (reliableTalent && adjustedRoll < 10) {
      adjustedRoll = 10;
    }

    const total = adjustedRoll + totalBonus;
    const success = total >= dc;

    return {
      type: 'skill_check',
      character: character.name,
      skill,
      ability,
      dc,
      roll,
      adjustedRoll,
      bonus: totalBonus,
      total,
      success,
      critical: roll.isCritical,
      fumble: roll.isFumble,
      degreeOfSuccess: AbilityChecks.calculateDegreeOfSuccess(total, dc),
      reliableTalent: reliableTalent && roll.total < 10
    };
  }

  /**
   * Perform a contested skill check
   * @param {Character} character1 - First character
   * @param {string} skill1 - First character's skill
   * @param {Character} character2 - Second character
   * @param {string} skill2 - Second character's skill
   * @param {object} options - Additional options
   * @returns {object} Contest result
   */
  static performContest(character1, skill1, character2, skill2, options = {}) {
    const check1 = this.performCheck(character1, skill1, 0, options);
    const check2 = this.performCheck(character2, skill2, 0, options);

    const winner = check1.total > check2.total ? character1.name :
                   check2.total > check1.total ? character2.name : 'tie';

    return {
      type: 'contested_skill_check',
      contestant1: {
        character: character1.name,
        skill: skill1,
        result: check1
      },
      contestant2: {
        character: character2.name,
        skill: skill2,
        result: check2
      },
      winner,
      margin: Math.abs(check1.total - check2.total)
    };
  }

  /**
   * Perform a group skill check
   * @param {Character[]} characters - Array of characters
   * @param {string} skill - Skill to check
   * @param {number} dc - Difficulty class
   * @param {number} requiredSuccesses - Number of successes needed
   * @param {object} options - Additional options
   * @returns {object} Group check result
   */
  static performGroupCheck(characters, skill, dc, requiredSuccesses, options = {}) {
    const results = characters.map(character =>
      this.performCheck(character, skill, dc, options)
    );

    const successes = results.filter(result => result.success).length;
    const success = successes >= requiredSuccesses;

    return {
      type: 'group_skill_check',
      skill,
      dc,
      requiredSuccesses,
      characters: characters.map(c => c.name),
      results,
      successes,
      failures: results.length - successes,
      success,
      outcome: success ? 'succeeded' : 'failed'
    };
  }

  /**
   * Calculate passive skill score
   * @param {Character} character - Character to calculate for
   * @param {string} skill - Skill to calculate
   * @param {number} bonus - Additional bonus
   * @returns {number} Passive skill score
   */
  static calculatePassiveScore(character, skill, bonus = 0) {
    const skillBonus = character.getSkillBonus(skill);
    return 10 + skillBonus + bonus;
  }

  /**
   * Get skill information
   * @param {string} skill - Skill name
   * @returns {object} Skill information
   */
  static getSkillInfo(skill) {
    const skillData = {
      [SKILLS.ATHLETICS]: {
        name: 'Athletics',
        ability: ABILITIES.STRENGTH,
        description: 'Covers difficult situations like climbing, jumping, and swimming',
        examples: ['Climbing a cliff', 'Jumping a chasm', 'Swimming in rough water']
      },
      [SKILLS.ACROBATICS]: {
        name: 'Acrobatics',
        ability: ABILITIES.DEXTERITY,
        description: 'Covers attempts to stay on feet in tricky situations',
        examples: ['Balancing on narrow surface', 'Diving from height', 'Escaping restraints']
      },
      [SKILLS.SLEIGHT_OF_HAND]: {
        name: 'Sleight of Hand',
        ability: ABILITIES.DEXTERITY,
        description: 'Covers acts of legerdemain and manual trickery',
        examples: ['Planting an object', 'Pickpocketing', 'Concealing object']
      },
      [SKILLS.STEALTH]: {
        name: 'Stealth',
        ability: ABILITIES.DEXTERITY,
        description: 'Covers attempts to conceal yourself from enemies',
        examples: ['Hiding from sight', 'Moving silently', 'Concealing approach']
      },
      [SKILLS.ARCANA]: {
        name: 'Arcana',
        ability: ABILITIES.INTELLIGENCE,
        description: 'Covers knowledge about magic and magical effects',
        examples: ['Identifying magic item', 'Understanding spell', 'Magical theory']
      },
      [SKILLS.HISTORY]: {
        name: 'History',
        ability: ABILITIES.INTELLIGENCE,
        description: 'Covers knowledge about historical events, people, and legends',
        examples: ['Ancient ruins', 'Royal lineage', 'Historical battles']
      },
      [SKILLS.INVESTIGATION]: {
        name: 'Investigation',
        ability: ABILITIES.INTELLIGENCE,
        description: 'Covers deductions about surroundings and situations',
        examples: ['Finding clues', 'Analyzing evidence', 'Deductive reasoning']
      },
      [SKILLS.NATURE]: {
        name: 'Nature',
        ability: ABILITIES.INTELLIGENCE,
        description: 'Covers knowledge about terrain, plants, and animals',
        examples: ['Identifying plants', 'Animal behavior', 'Weather patterns']
      },
      [SKILLS.RELIGION]: {
        name: 'Religion',
        ability: ABILITIES.INTELLIGENCE,
        description: 'Covers knowledge about deities, religious traditions, and planes',
        examples: ['Deity identification', 'Religious rituals', 'Planar knowledge']
      },
      [SKILLS.ANIMAL_HANDLING]: {
        name: 'Animal Handling',
        ability: ABILITIES.WISDOM,
        description: 'Covers working with animals and calming them',
        examples: ['Calming frightened animal', 'Training animal', 'Animal behavior']
      },
      [SKILLS.INSIGHT]: {
        name: 'Insight',
        ability: ABILITIES.WISDOM,
        description: 'Covers determining true intentions and character',
        examples: ['Detecting lies', 'Reading body language', 'Understanding motives']
      },
      [SKILLS.MEDICINE]: {
        name: 'Medicine',
        ability: ABILITIES.WISDOM,
        description: 'Covers diagnoses and treatment of wounds and ailments',
        examples: ['First aid', 'Diagnosing illness', 'Treating wounds']
      },
      [SKILLS.PERCEPTION]: {
        name: 'Perception',
        ability: ABILITIES.WISDOM,
        description: 'Covers awareness of surroundings and keen senses',
        examples: ['Spotting hidden creature', 'Noticing details', 'Hearing sounds']
      },
      [SKILLS.SURVIVAL]: {
        name: 'Survival',
        ability: ABILITIES.WISDOM,
        description: 'Covers knowledge of tracking, hunting, and wilderness survival',
        examples: ['Finding food', 'Tracking prey', 'Navigating wilderness']
      },
      [SKILLS.DECEPTION]: {
        name: 'Deception',
        ability: ABILITIES.CHARISMA,
        description: 'Covers attempts to hide truth or mislead others',
        examples: ['Lying convincingly', 'Hiding motives', 'Creating diversions']
      },
      [SKILLS.INTIMIDATION]: {
        name: 'Intimidation',
        ability: ABILITIES.CHARISMA,
        description: 'Covers attempts to influence through threats',
        examples: ['Scaring someone', 'Making threats', 'Showing dominance']
      },
      [SKILLS.PERFORMANCE]: {
        name: 'Performance',
        ability: ABILITIES.CHARISMA,
        description: 'Covers artistic expression and entertainment',
        examples: ['Playing instrument', 'Acting', 'Singing', 'Dancing']
      },
      [SKILLS.PERSUASION]: {
        name: 'Persuasion',
        ability: ABILITIES.CHARISMA,
        description: 'Covers attempts to influence through reasoning or charm',
        examples: ['Convincing someone', 'Negotiating', 'Making requests']
      }
    };

    return skillData[skill] || null;
  }

  /**
   * Get skill specialties and advanced uses
   * @param {string} skill - Skill name
   * @returns {object} Specialized information
   */
  static getSkillSpecialties(skill) {
    const specialties = {
      [SKILLS.PERCEPTION]: {
        specialties: ['sight', 'sound', 'smell', 'investigation'],
        passiveUses: ['spotting ambushes', 'noticing details', 'detecting invisible creatures']
      },
      [SKILLS.STEALTH]: {
        specialties: ['hiding', 'moving silently', 'concealment'],
        advancedTechniques: ['using cover', 'opportunity timing', 'distraction usage']
      },
      [SKILLS.INVESTIGATION]: {
        specialties: ['forensic', 'deductive', 'analytical'],
        tools: ['magnifying glass', 'crime scene kit', 'research materials']
      },
      [SKILLS.ARCANA]: {
        specialties: ['identification', 'theory', 'history', 'planes'],
        applications: ['magic item analysis', 'spell research', 'rune decoding']
      }
    };

    return specialties[skill] || { specialties: [], advancedTechniques: [] };
  }
}

export default SkillChecks;