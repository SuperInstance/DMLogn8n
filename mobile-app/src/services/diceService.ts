import { DiceRoll } from '../types';

export class DiceService {
  private static instance: DiceService;

  private constructor() {}

  static getInstance(): DiceService {
    if (!DiceService.instance) {
      DiceService.instance = new DiceService();
    }
    return DiceService.instance;
  }

  // Roll a single die
  static rollD20(): number {
    return Math.floor(Math.random() * 20) + 1;
  }

  static rollDice(sides: number): number {
    return Math.floor(Math.random() * sides) + 1;
  }

  // Roll multiple dice
  static rollMultipleDice(sides: number, count: number): number[] {
    const results: number[] = [];
    for (let i = 0; i < count; i++) {
      results.push(this.rollDice(sides));
    }
    return results;
  }

  // Roll with advantage
  static rollWithAdvantage(): { roll1: number; roll2: number; result: number; hasAdvantage: boolean } {
    const roll1 = this.rollD20();
    const roll2 = this.rollD20();
    const result = Math.max(roll1, roll2);
    const hasAdvantage = result > 10; // Simple check for "advantage"

    return { roll1, roll2, result, hasAdvantage };
  }

  // Roll with disadvantage
  static rollWithDisadvantage(): { roll1: number; roll2: number; result: number; hasDisadvantage: boolean } {
    const roll1 = this.rollD20();
    const roll2 = this.rollD20();
    const result = Math.min(roll1, roll2);
    const hasDisadvantage = result < 11; // Simple check for "disadvantage"

    return { roll1, roll2, result, hasDisadvantage };
  }

  // Parse dice formula
  static parseFormula(formula: string): {
    dice: { sides: number; count: number }[];
    modifier: number;
  } {
    const dice: { sides: number; count: number }[] = [];
    let modifier = 0;

    // Remove spaces
    const cleanFormula = formula.replace(/\s/g, '');

    // Find all dice patterns (e.g., "2d6", "d20", "1d8+3")
    const dicePattern = /(\d*)d(\d+)([+-]\d+)?/g;
    let match;

    while ((match = dicePattern.exec(cleanFormula)) !== null) {
      const count = match[1] ? parseInt(match[1]) : 1;
      const sides = parseInt(match[2]);
      const modStr = match[3];

      dice.push({ sides, count });

      if (modStr) {
        modifier += parseInt(modStr);
      }
    }

    // Check for standalone modifier
    const standaloneModifier = cleanFormula.match(/([+-]\d+)$/);
    if (standaloneModifier) {
      modifier += parseInt(standaloneModifier[1]);
    }

    return { dice, modifier };
  }

  // Roll based on formula
  static rollFormula(formula: string): DiceRoll {
    const { dice, modifier } = this.parseFormula(formula);
    const rolls: { type: string; value: number; rolled: number }[] = [];
    let total = modifier;

    // Roll each dice group
    dice.forEach(die => {
      for (let i = 0; i < die.count; i++) {
        const rolled = this.rollDice(die.sides);
        total += rolled;
        rolls.push({
          type: `d${die.sides}`,
          value: rolled,
          rolled,
        });
      }
    });

    // Check for critical success/fumble on d20
    const d20Rolls = rolls.filter(r => r.type === 'd20');
    const isCritical = d20Rolls.some(r => r.value === 20);
    const isFumble = d20Rolls.some(r => r.value === 1);

    return {
      id: `dice_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      userId: 'current-user',
      type: formula,
      formula,
      rolls,
      total,
      modifier,
      reason: 'Manual Roll',
      timestamp: new Date().toISOString(),
      isCritical,
      isFumble,
    };
  }

  // Get dice probability
  static getDiceProbability(sides: number, target: number): number {
    if (target < 1) return 1;
    if (target > sides) return 0;
    return (sides - target + 1) / sides;
  }

  // Get average roll for dice
  static getAverageRoll(sides: number, count: number = 1): number {
    return ((sides + 1) / 2) * count;
  }

  // Get roll statistics
  static getRollStatistics(rolls: number[]): {
    average: number;
    min: number;
    max: number;
    median: number;
    mode: number[];
  } {
    if (rolls.length === 0) {
      return { average: 0, min: 0, max: 0, median: 0, mode: [] };
    }

    const sorted = [...rolls].sort((a, b) => a - b);
    const sum = rolls.reduce((acc, val) => acc + val, 0);
    const average = sum / rolls.length;
    const min = sorted[0];
    const max = sorted[sorted.length - 1];

    // Median
    const mid = Math.floor(sorted.length / 2);
    const median = sorted.length % 2 === 0
      ? (sorted[mid - 1] + sorted[mid]) / 2
      : sorted[mid];

    // Mode
    const frequency: Record<number, number> = {};
    let maxFreq = 0;
    const modes: number[] = [];

    rolls.forEach(val => {
      frequency[val] = (frequency[val] || 0) + 1;
      if (frequency[val] > maxFreq) {
        maxFreq = frequency[val];
      }
    });

    Object.keys(frequency).forEach(key => {
      const val = parseInt(key);
      if (frequency[val] === maxFreq) {
        modes.push(val);
      }
    });

    return { average, min, max, median, mode: modes };
  }

  // Validate dice formula
  static validateFormula(formula: string): {
    isValid: boolean;
    error?: string;
  } {
    if (!formula || formula.trim() === '') {
      return { isValid: false, error: 'Formula cannot be empty' };
    }

    const cleanFormula = formula.replace(/\s/g, '').toLowerCase();

    // Check for valid characters only
    if (!/^[0-9d+\-]+$/.test(cleanFormula)) {
      return { isValid: false, error: 'Formula contains invalid characters' };
    }

    // Check for valid dice format
    const dicePattern = /(\d*)d(\d+)/g;
    let match;
    const diceFound = [];

    while ((match = dicePattern.exec(cleanFormula)) !== null) {
      const count = match[1] ? parseInt(match[1]) : 1;
      const sides = parseInt(match[2]);

      if (count < 1 || count > 100) {
        return { isValid: false, error: 'Dice count must be between 1 and 100' };
      }

      if (sides < 2 || sides > 1000) {
        return { isValid: false, error: 'Dice sides must be between 2 and 1000' };
      }

      diceFound.push({ count, sides });
    }

    if (diceFound.length === 0) {
      return { isValid: false, error: 'No dice found in formula' };
    }

    return { isValid: true };
  }

  // Get common dice formulas
  static getCommonFormulas(): Array<{
    name: string;
    formula: string;
    description: string;
  }> {
    return [
      {
        name: 'Attack Roll',
        formula: 'd20',
        description: 'Standard attack roll',
      },
      {
        name: 'Attack with Advantage',
        formula: '2d20kh1',
        description: 'Roll two d20, keep highest',
      },
      {
        name: 'Attack with Disadvantage',
        formula: '2d20kl1',
        description: 'Roll two d20, keep lowest',
      },
      {
        name: 'Skill Check',
        formula: 'd20',
        description: 'Standard skill check',
      },
      {
        name: 'Damage (Shortsword)',
        formula: '1d6',
        description: 'Shortsword damage',
      },
      {
        name: 'Damage (Greatsword)',
        formula: '2d6',
        description: 'Greatsword damage',
      },
      {
        name: 'Damage (Fireball)',
        formula: '8d6',
        description: 'Fireball damage',
      },
      {
        name: 'Healing (Cure Wounds)',
        formula: '1d8',
        description: 'Cure wounds healing',
      },
      {
        name: 'Hit Dice (Level 1-10)',
        formula: 'd8',
        description: 'Hit dice for short rest',
      },
      {
        name: 'Initiative',
        formula: 'd20',
        description: 'Combat initiative',
      },
      {
        name: 'Death Save',
        formula: 'd20',
        description: 'Death saving throw',
      },
      {
        name: 'Critical Hit (Greatsword)',
        formula: '4d6',
        description: 'Critical hit damage for 2d6 weapon',
      },
    ];
  }

  // Simulate multiple rolls for statistics
  static simulateRolls(formula: string, iterations: number = 1000): {
    rolls: number[];
    statistics: {
      average: number;
      min: number;
      max: number;
      median: number;
      mode: number[];
    };
    distribution: Record<string, number>;
  } {
    const rolls: number[] = [];

    for (let i = 0; i < iterations; i++) {
      const result = this.rollFormula(formula);
      rolls.push(result.total);
    }

    const statistics = this.getRollStatistics(rolls);

    // Create distribution
    const distribution: Record<string, number> = {};
    rolls.forEach(roll => {
      const key = roll.toString();
      distribution[key] = (distribution[key] || 0) + 1;
    });

    // Convert to percentages
    Object.keys(distribution).forEach(key => {
      distribution[key] = (distribution[key] / iterations) * 100;
    });

    return { rolls, statistics, distribution };
  }
}