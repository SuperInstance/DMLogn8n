/**
 * Dice rolling system for D&D 5e
 */

export class DiceRoller {
  /**
   * Roll a d20 with optional advantage/disadvantage
   * @param {number} advantage - -1 for disadvantage, 0 for normal, 1 for advantage
   * @returns {object} Roll result with details
   */
  static rollD20(advantage = 0) {
    const rolls = [];

    if (advantage > 0) {
      // Advantage - roll twice, take higher
      rolls.push(this.rollDie(20));
      rolls.push(this.rollDie(20));
    } else if (advantage < 0) {
      // Disadvantage - roll twice, take lower
      rolls.push(this.rollDie(20));
      rolls.push(this.rollDie(20));
    } else {
      // Normal roll
      rolls.push(this.rollDie(20));
    }

    const result = {
      rolls,
      advantage,
      total: advantage > 0 ? Math.max(...rolls) : advantage < 0 ? Math.min(...rolls) : rolls[0],
      natural20: rolls.includes(20),
      natural1: rolls.includes(1),
      isCritical: advantage > 0 ? rolls.some(r => r === 20) : advantage < 0 ? rolls.every(r => r === 20) : rolls[0] === 20,
      isFumble: advantage > 0 ? rolls.every(r => r === 1) : advantage < 0 ? rolls.some(r => r === 1) : rolls[0] === 1
    };

    return result;
  }

  /**
   * Roll a custom dice expression (e.g., "2d6+3", "1d8-1", "4d4")
   * @param {string} expression - Dice expression to parse
   * @returns {object} Roll result
   */
  static rollExpression(expression) {
    const cleanExpression = expression.toLowerCase().replace(/\s/g, '');

    // Parse the expression
    const match = cleanExpression.match(/^(\d+)d(\d+)([+-]\d+)?$/);
    if (!match) {
      throw new Error(`Invalid dice expression: ${expression}`);
    }

    const [_, numDice, dieSize, modifier] = match;
    const num = parseInt(numDice);
    const size = parseInt(dieSize);
    const mod = modifier ? parseInt(modifier) : 0;

    // Roll the dice
    const rolls = [];
    for (let i = 0; i < num; i++) {
      rolls.push(this.rollDie(size));
    }

    const total = rolls.reduce((sum, roll) => sum + roll, 0) + mod;

    return {
      expression,
      numDice: num,
      dieSize: size,
      modifier: mod,
      rolls,
      total,
      average: total / num
    };
  }

  /**
   * Roll damage with critical hit handling
   * @param {string} damageExpression - Damage dice expression
   * @param {boolean} critical - Whether this is a critical hit
   * @param {number} criticalMultiplier - Critical hit damage multiplier (default 2)
   * @returns {object} Damage result
   */
  static rollDamage(damageExpression, critical = false, criticalMultiplier = 2) {
    const baseResult = this.rollExpression(damageExpression);

    if (critical) {
      // Roll the damage dice again for critical
      const critResult = this.rollExpression(damageExpression);
      const critRolls = [...baseResult.rolls, ...critResult.rolls];

      return {
        ...baseResult,
        critical: true,
        rolls: critRolls,
        baseDamage: baseResult.total,
        criticalDamage: critResult.total,
        total: baseResult.total + critResult.total + baseResult.modifier
      };
    }

    return {
      ...baseResult,
      critical: false
    };
  }

  /**
   * Roll a single die
   * @param {number} sides - Number of sides on the die
   * @returns {number} Roll result
   */
  static rollDie(sides) {
    return Math.floor(Math.random() * sides) + 1;
  }

  /**
   * Roll multiple dice and sum them
   * @param {number} numDice - Number of dice to roll
   * @param {number} dieSize - Size of each die
   * @returns {object} Roll result
   */
  static rollDice(numDice, dieSize) {
    const rolls = [];
    for (let i = 0; i < numDice; i++) {
      rolls.push(this.rollDie(dieSize));
    }

    return {
      numDice,
      dieSize,
      rolls,
      total: rolls.reduce((sum, roll) => sum + roll, 0),
      average: rolls.reduce((sum, roll) => sum + roll, 0) / numDice
    };
  }

  /**
   * Calculate probability of success for a given DC
   * @param {number} bonus - Total bonus to the roll
   * @param {number} dc - Difficulty class
   * @param {number} advantage - -1 disadvantage, 0 normal, 1 advantage
   * @returns {number} Probability of success (0-1)
   */
  static calculateSuccessProbability(bonus, dc, advantage = 0) {
    const targetNumber = dc - bonus;

    if (advantage > 0) {
      // Advantage probability
      if (targetNumber <= 1) return 1;
      if (targetNumber > 20) return 0;
      const failChance = ((targetNumber - 1) / 20) ** 2;
      return 1 - failChance;
    } else if (advantage < 0) {
      // Disadvantage probability
      if (targetNumber <= 1) return 1;
      if (targetNumber > 20) return 0;
      const successChance = ((21 - targetNumber) / 20) ** 2;
      return successChance;
    } else {
      // Normal probability
      if (targetNumber <= 1) return 1;
      if (targetNumber > 20) return 0;
      return (21 - targetNumber) / 20;
    }
  }

  /**
   * Generate statistical analysis of dice rolls
   * @param {string} expression - Dice expression
   * @param {number} iterations - Number of simulated rolls
   * @returns {object} Statistical analysis
   */
  static analyzeDice(expression, iterations = 10000) {
    const results = [];

    for (let i = 0; i < iterations; i++) {
      results.push(this.rollExpression(expression).total);
    }

    results.sort((a, b) => a - b);

    const mean = results.reduce((sum, val) => sum + val, 0) / results.length;
    const variance = results.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / results.length;
    const stdDev = Math.sqrt(variance);

    return {
      expression,
      iterations,
      mean,
      median: results[Math.floor(results.length / 2)],
      min: results[0],
      max: results[results.length - 1],
      standardDeviation: stdDev,
      percentiles: {
        5: results[Math.floor(results.length * 0.05)],
        25: results[Math.floor(results.length * 0.25)],
        50: results[Math.floor(results.length * 0.5)],
        75: results[Math.floor(results.length * 0.75)],
        95: results[Math.floor(results.length * 0.95)]
      }
    };
  }
}

export default DiceRoller;