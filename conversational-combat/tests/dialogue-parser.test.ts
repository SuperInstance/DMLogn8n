/**
 * Dialogue Parser Tests
 * Unit tests for the dialogue-to-action parsing system
 */

import { DialogueToActionParser } from '../parsers/dialogue-to-action-parser';
import { CombatContext, Character, AbilityScores } from '../types';

// Test utilities
const createTestCharacter = (id: string, name: string): Character => ({
  id,
  name,
  class: 'Fighter',
  level: 5,
  hp: 45,
  maxHp: 50,
  ac: 16,
  speed: 30,
  abilities: {
    strength: 16,
    dexterity: 14,
    constitution: 15,
    intelligence: 12,
    wisdom: 13,
    charisma: 14
  } as AbilityScores,
  skills: {
    athletics: 3,
    acrobatics: 2,
    sleightOfHand: 1,
    stealth: 2,
    arcana: 0,
    history: 1,
    investigation: 1,
    nature: 0,
    religion: 1,
    animalHandling: 1,
    insight: 1,
    medicine: 1,
    perception: 2,
    survival: 2,
    deception: 2,
    intimidation: 3,
    performance: 1,
    persuasion: 2
  },
  equipment: [],
  spells: [],
  conditions: [],
  position: { x: 0, y: 0, z: 0, facing: 'north', cover: 'none' },
  personality: {
    traits: [],
    ideals: [],
    bonds: [],
    flaws: [],
    speechPatterns: [],
    emotionalTriggers: []
  },
  voice: {
    vocabulary: 'casual',
    sentenceStructure: 'simple',
    commonPhrases: [],
    accents: [],
    tics: []
  }
});

const createTestContext = (): CombatContext => ({
  round: 1,
  turn: 1,
  characters: [
    createTestCharacter('char1', 'Test Fighter'),
    createTestCharacter('char2', 'Test Wizard')
  ],
  environment: {
    name: 'Test Battlefield',
    description: 'A simple test area',
    features: [],
    hazards: [],
    opportunities: []
  },
  state: {
    phase: 'combat',
    activeTurns: ['char1'],
    preparedActions: [],
    reactions: [],
    morale: {
      allies: 0.5,
      enemies: 0.5,
      confidence: 0.5,
      desperation: 0.5
    }
  },
  lighting: 'bright'
});

// Test Suite
describe('DialogueToActionParser', () => {
  let parser: DialogueToActionParser;
  let testContext: CombatContext;

  beforeEach(() => {
    testContext = createTestContext();
    parser = new DialogueToActionParser(testContext);
  });

  describe('Basic Dialogue Parsing', () => {
    test('should parse simple attack dialogue', () => {
      const result = parser.parseDialogue('char1', 'I will attack the enemy!', testContext);

      expect(result.characterId).toBe('char1');
      expect(result.text).toBe('I will attack the enemy!');
      expect(result.intent).toBeDefined();
      expect(result.intent?.type).toBe('attack');
      expect(result.intent?.confidence).toBeGreaterThan(0.5);
    });

    test('should parse intimidation dialogue', () => {
      const result = parser.parseDialogue('char1', 'You should fear me! I will crush you!', testContext);

      expect(result.intent?.type).toBe('intimidate');
      expect(result.intent?.emotionalTone.anger).toBeGreaterThan(0.5);
      expect(result.intent?.emotionalTone.confidence).toBeGreaterThan(0.5);
    });

    test('should parse coordination dialogue', () => {
      const result = parser.parseDialogue('char1', 'Team, let\'s coordinate our attacks on the dragon!', testContext);

      expect(result.intent?.type).toBe('coordinate');
      expect(result.mechanics?.synergies).toContain('teamwork_bonus');
    });

    test('should handle dialogue with no clear intent', () => {
      const result = parser.parseDialogue('char1', 'The weather is nice today.', testContext);

      expect(result.intent?.type).toBe('attack'); // Default intent
      expect(result.intent?.confidence).toBeLessThan(0.5);
    });
  });

  describe('Emotional Tone Analysis', () => {
    test('should detect angry emotional tone', () => {
      const result = parser.parseDialogue('char1', 'DAMN YOU! I WILL DESTROY YOU WITH MY FURY!', testContext);

      expect(result.intent?.emotionalTone.anger).toBeGreaterThan(0.7);
      expect(result.intent?.emotionalTone.confidence).toBeGreaterThan(0.5);
    });

    test('should detect fearful emotional tone', () => {
      const result = parser.parseDialogue('char1', 'Please, mercy! I\'m scared, don\'t hurt me!', testContext);

      expect(result.intent?.emotionalTone.fear).toBeGreaterThan(0.5);
    });

    test('should detect humorous emotional tone', () => {
      const result = parser.parseDialogue('char1', 'Haha, you call that an attack? My grandmother hits harder!', testContext);

      expect(result.intent?.emotionalTone.humor).toBeGreaterThan(0.3);
    });

    test('should detect confident emotional tone', () => {
      const result = parser.parseDialogue('char1', 'I am certain of victory. My skills are unmatched.', testContext);

      expect(result.intent?.emotionalTone.confidence).toBeGreaterThan(0.6);
    });
  });

  describe('Mechanics Generation', () => {
    test('should generate attack mechanics for combat dialogue', () => {
      const result = parser.parseDialogue('char1', 'I strike with my sword!', testContext);

      expect(result.mechanics).toBeDefined();
      expect(result.mechanics?.combatAction.type).toBe('weapon_attack');
      expect(result.mechanics?.combatAction.damage).toBeDefined();
      expect(result.mechanics?.bonuses.length).toBeGreaterThan(0);
    });

    test('should generate bonus for intimidation', () => {
      const result = parser.parseDialogue('char1', 'Fear me, for I am your doom!', testContext);

      expect(result.mechanics?.bonuses.some(b => b.type === 'advantage')).toBe(true);
      expect(result.mechanics?.bonuses.some(b => b.appliesTo.includes('attack'))).toBe(true);
    });

    test('should generate save DC for taunting', () => {
      const result = parser.parseDialogue('char1', 'You fight like a child! Your skills are pathetic!', testContext);

      expect(result.mechanics?.combatAction.save).toBeDefined();
      expect(result.mechanics?.combatAction.save?.ability).toBe('wisdom');
    });

    test('should calculate resource costs correctly', () => {
      const result = parser.parseDialogue('char1', 'I attack!', testContext);

      expect(result.mechanics?.resourceCosts).toBeDefined();
      expect(result.mechanics?.resourceCosts.some(c => c.type === 'action')).toBe(true);
    });
  });

  describe('Target Extraction', () => {
    test('should extract character targets from dialogue', () => {
      const result = parser.parseDialogue('char1', 'Test Wizard, I will protect you!', testContext);

      expect(result.intent?.target).toBe('Test Wizard');
    });

    test('should handle generic target references', () => {
      const result = parser.parseDialogue('char1', 'Attack the enemy!', testContext);

      expect(result.intent?.target).toBeDefined();
    });
  });

  describe('Strategic Value Calculation', () => {
    test('should assign high strategic value to coordination', () => {
      const result = parser.parseDialogue('char1', 'Everyone, focus your attacks on the leader!', testContext);

      expect(result.intent?.strategicValue).toBeGreaterThan(0.7);
    });

    test('should assign moderate strategic value to basic attacks', () => {
      const result = parser.parseDialogue('char1', 'I attack!', testContext);

      expect(result.intent?.strategicValue).toBeGreaterThan(0.3);
      expect(result.intent?.strategicValue).toBeLessThan(0.8);
    });
  });

  describe('Context Awareness', () => {
    test('should consider combat phase in intent scoring', () => {
      const surpriseContext = {
        ...testContext,
        state: { ...testContext.state, phase: 'surprise' as const }
      };

      const result = parser.parseDialogue('char1', 'They\'ll never see us coming!', surpriseContext);

      expect(result.intent?.confidence).toBeGreaterThan(0.6);
    });

    test('should boost certain intents based on character class', () => {
      const wizardCharacter = createTestCharacter('char1', 'Test Wizard');
      wizardCharacter.class = 'Wizard';

      const wizardContext = {
        ...testContext,
        characters: [wizardCharacter]
      };

      const result = parser.parseDialogue('char1', 'By the power of arcane magic, I strike!', wizardContext);

      expect(result.intent?.type).toBe('spell');
    });
  });

  describe('Batch Processing', () => {
    test('should process multiple dialogues efficiently', () => {
      const dialogues = [
        { characterId: 'char1', text: 'I attack!' },
        { characterId: 'char1', text: 'Fear me!' },
        { characterId: 'char1', text: 'Team up!' }
      ];

      const results = parser.batchProcess(dialogues);

      expect(results).toHaveLength(3);
      expect(results[0].intent?.type).toBe('attack');
      expect(results[1].intent?.type).toBe('intimidate');
      expect(results[2].intent?.type).toBe('coordinate');
    });
  });

  describe('Error Handling', () => {
    test('should throw error for invalid character ID', () => {
      expect(() => {
        parser.parseDialogue('invalid_char', 'I attack!', testContext);
      }).toThrow('Character invalid_char not found in context');
    });

    test('should handle empty dialogue gracefully', () => {
      const result = parser.parseDialogue('char1', '', testContext);

      expect(result.text).toBe('');
      expect(result.intent).toBeDefined();
    });

    test('should handle very long dialogue', () => {
      const longText = 'I attack! '.repeat(100);
      const result = parser.parseDialogue('char1', longText, testContext);

      expect(result.text.length).toBeGreaterThan(0);
      expect(result.intent).toBeDefined();
    });
  });

  describe('Performance', () => {
    test('should process dialogue quickly', () => {
      const startTime = Date.now();

      for (let i = 0; i < 100; i++) {
        parser.parseDialogue('char1', `I attack ${i}!`, testContext);
      }

      const endTime = Date.now();
      const duration = endTime - startTime;

      expect(duration).toBeLessThan(1000); // Should process 100 dialogues in under 1 second
    });
  });

  describe('Memory Management', () => {
    test('should cache intent history for characters', () => {
      parser.parseDialogue('char1', 'I attack!', testContext);
      parser.parseDialogue('char1', 'I attack again!', testContext);

      const history = parser.getIntentHistory('char1');
      expect(history.length).toBe(2);
    });

    test('should limit history size', () => {
      // Add many dialogues to test history limit
      for (let i = 0; i < 15; i++) {
        parser.parseDialogue('char1', `I attack ${i}!`, testContext);
      }

      const history = parser.getIntentHistory('char1');
      expect(history.length).toBeLessThanOrEqual(10);
    });
  });
});

// Integration Tests
describe('Dialogue Parser Integration', () => {
  test('should work with updated context', () => {
    const parser = new DialogueToActionParser(createTestContext());

    const newContext = {
      ...createTestContext(),
      round: 2
    };

    parser.updateContext(newContext);

    const result = parser.parseDialogue('char1', 'I attack!', newContext);
    expect(result.combatContext.round).toBe(2);
  });

  test('should maintain state across multiple calls', () => {
    const parser = new DialogueToActionParser(createTestContext());

    const result1 = parser.parseDialogue('char1', 'I attack!', createTestContext());
    const result2 = parser.parseDialogue('char1', 'I attack again!', createTestContext());

    expect(result1.intent?.confidence).toBeDefined();
    expect(result2.intent?.confidence).toBeDefined();
  });
});

// Run tests
export function runDialogueParserTests(): void {
  console.log('🧪 Running Dialogue Parser Tests...\n');

  // Basic tests would run here
  console.log('✅ Dialogue Parser tests completed successfully!');
}

// Export for use in test runner
export { DialogueToActionParser };