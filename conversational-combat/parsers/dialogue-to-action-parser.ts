/**
 * Dialogue-to-Action Parser with Natural Language Processing
 * Transforms conversational input into combat mechanics
 */

import {
  CombatDialogue,
  DialogueIntent,
  DialogueMechanics,
  CombatAction,
  EmotionalTone,
  CombatContext,
  Character,
  MechanicalBonus,
  ResourceCost
} from '../types';
import { DIALOGUE_PATTERNS, EMOTIONAL_KEYWORDS, ACTION_MAPPINGS, DIALOGUE_BONUSES, DIALOGUE_DAMAGE_TYPES } from '../utils/constants';

export class DialogueToActionParser {
  private context: CombatContext;
  private characterCache: Map<string, Character> = new Map();
  private intentCache: Map<string, DialogueIntent[]> = new Map();

  constructor(context: CombatContext) {
    this.context = context;
    this.initializeCharacterCache();
  }

  /**
   * Parse dialogue text and extract combat-relevant information
   */
  public parseDialogue(
    characterId: string,
    text: string,
    combatContext: CombatContext
  ): CombatDialogue {
    const character = this.characterCache.get(characterId);
    if (!character) {
      throw new Error(`Character ${characterId} not found in context`);
    }

    const intent = this.extractIntent(text, character, combatContext);
    const mechanics = intent ? this.generateMechanics(intent, character, combatContext) : undefined;

    return {
      id: this.generateDialogueId(),
      characterId,
      text,
      timestamp: new Date(),
      combatContext,
      intent,
      mechanics
    };
  }

  /**
   * Extract combat intent from dialogue text
   */
  private extractIntent(text: string, character: Character, context: CombatContext): DialogueIntent {
    const lowerText = text.toLowerCase();
    const emotionalTone = this.analyzeEmotionalTone(text);

    // Calculate intent type based on patterns and context
    const intentType = this.determineIntentType(lowerText, character, context);
    const target = this.extractTarget(lowerText, context);
    const action = this.extractAction(lowerText, intentType);
    const flavor = this.extractFlavorText(text);

    // Calculate confidence based on pattern matching and context
    const confidence = this.calculateIntentConfidence(lowerText, intentType, context);

    // Calculate strategic value based on combat state
    const strategicValue = this.calculateStrategicValue(intentType, emotionalTone, context);

    return {
      type: intentType,
      target,
      action,
      flavor,
      confidence,
      emotionalTone,
      strategicValue
    };
  }

  /**
   * Analyze emotional tone of dialogue
   */
  private analyzeEmotionalTone(text: string): EmotionalTone {
    const lowerText = text.toLowerCase();
    const words = lowerText.split(/\s+/);

    let anger = 0, confidence = 0, fear = 0, humor = 0, seriousness = 0, desperation = 0;

    // Count emotional keywords
    for (const word of words) {
      if (EMOTIONAL_KEYWORDS.anger.some(angerWord => word.includes(angerWord))) anger++;
      if (EMOTIONAL_KEYWORDS.confidence.some(confWord => word.includes(confWord))) confidence++;
      if (EMOTIONAL_KEYWORDS.fear.some(fearWord => word.includes(fearWord))) fear++;
      if (EMOTIONAL_KEYWORDS.humor.some(humorWord => word.includes(humorWord))) humor++;
      if (EMOTIONAL_KEYWORDS.seriousness.some(seriousWord => word.includes(seriousWord))) seriousness++;
      if (EMOTIONAL_KEYWORDS.desperation.some(despWord => word.includes(despWord))) desperation++;
    }

    // Analyze punctuation and capitalization for additional emotional indicators
    const exclamationCount = (text.match(/!/g) || []).length;
    const allCapsCount = (text.match(/[A-Z]{3,}/g) || []).length;
    const questionCount = (text.match(/\?/g) || []).length;

    // Adjust scores based on text characteristics
    anger += (exclamationCount * 0.2) + (allCapsCount * 0.3);
    humor += (questionCount * 0.1);
    desperation += (exclamationCount * 0.1) + (allCapsCount * 0.1);

    // Normalize to 0-1 range
    const total = Math.max(1, words.length);
    return {
      anger: Math.min(1, anger / total),
      confidence: Math.min(1, confidence / total),
      fear: Math.min(1, fear / total),
      humor: Math.min(1, humor / total),
      seriousness: Math.min(1, seriousness / total),
      desperation: Math.min(1, desperation / total)
    };
  }

  /**
   * Determine the primary intent type
   */
  private determineIntentType(text: string, character: Character, context: CombatContext): DialogueIntent['type'] {
    const scores: { [key in DialogueIntent['type']]: number } = {
      attack: 0,
      defend: 0,
      buff: 0,
      debuff: 0,
      taunt: 0,
      intimidate: 0,
      persuade: 0,
      deceive: 0,
      coordinate: 0,
      spell: 0
    };

    // Pattern matching for each intent type
    for (const [intentType, patterns] of Object.entries(DIALOGUE_PATTERNS)) {
      for (const pattern of patterns) {
        if (pattern.test(text)) {
          scores[intentType as DialogueIntent['type']] += 1;
        }
      }
    }

    // Context-based scoring
    if (context.state.phase === 'combat') {
      // Boost combat intents during active combat
      scores.attack *= 1.5;
      scores.defend *= 1.3;
      spells.spell *= 1.4;
    }

    // Character-based scoring
    const charClass = character.class.toLowerCase();
    if (charClass.includes('fighter') || charClass.includes('barbarian')) {
      scores.attack *= 1.3;
      scores.intimidate *= 1.2;
    } else if (charClass.includes('wizard') || charClass.includes('sorcerer')) {
      scores.spell *= 1.5;
    } else if (charClass.includes('rogue')) {
      scores.deceive *= 1.4;
      scores.taunt *= 1.2;
    } else if (charClass.includes('cleric') || charClass.includes('paladin')) {
      scores.buff *= 1.3;
      scores.persuade *= 1.2;
    }

    // Determine highest scoring intent
    let highestIntent: DialogueIntent['type'] = 'attack';
    let highestScore = 0;

    for (const [intent, score] of Object.entries(scores)) {
      if (score > highestScore) {
        highestScore = score;
        highestIntent = intent as DialogueIntent['type'];
      }
    }

    return highestScore > 0 ? highestIntent : 'attack';
  }

  /**
   * Extract target from dialogue text
   */
  private extractTarget(text: string, context: CombatContext): string | undefined {
    // Look for character names in context
    for (const character of context.characters) {
      if (text.toLowerCase().includes(character.name.toLowerCase())) {
        return character.id;
      }
    }

    // Look for generic target references
    const targetPatterns = [
      /(\byou\b|\byour\b)/i,
      /(\benemy\b|\bfoe\b|\badversary\b)/i,
      /(\ballies\b|\bfriends\b|\bcompanions\b)/i,
      /(\beveryone\b|\ball\b)/i
    ];

    for (const pattern of targetPatterns) {
      if (pattern.test(text)) {
        return pattern.source;
      }
    }

    return undefined;
  }

  /**
   * Extract specific action from dialogue
   */
  private extractAction(text: string, intentType: DialogueIntent['type']): string | undefined {
    const actionPatterns = {
      attack: [/(\battack\b|\bstrike\b|\bhit\b|\bslash\b|\bcharge\b)/i],
      defend: [/(\bblock\b|\bparry\b|\bdodge\b|\bguard\b)/i],
      spell: [/(\bcast\b|\butter\b|\bchant\b|\bspeak\b)/i],
      coordinate: [/(\bready\b|\bwait\b|\bcountdown\b)/i],
      intimidate: [/(\bfear\b|\bdoom\b|\bdeath\b)/i]
    };

    const patterns = actionPatterns[intentType] || [];
    for (const pattern of patterns) {
      const match = text.match(pattern);
      if (match) {
        return match[0];
      }
    }

    return undefined;
  }

  /**
   * Extract flavor text for narrative purposes
   */
  private extractFlavorText(text: string): string {
    // Remove common mechanical phrases and return flavorful portions
    const cleanedText = text
      .replace(/\b(attack|cast|defend|use|activate)\b/gi, '')
      .replace(/\bon my mark\b/gi, '')
      .replace(/\bready when you are\b/gi, '')
      .trim();

    return cleanedText || text;
  }

  /**
   * Calculate confidence score for intent extraction
   */
  private calculateIntentConfidence(
    text: string,
    intentType: DialogueIntent['type'],
    context: CombatContext
  ): number {
    let confidence = 0.5; // Base confidence

    // Pattern matching confidence
    const patterns = DIALOGUE_PATTERNS[intentType.toUpperCase() as keyof typeof DIALOGUE_PATTERNS];
    if (patterns) {
      for (const pattern of patterns) {
        if (pattern.test(text)) {
          confidence += 0.15;
        }
      }
    }

    // Context confidence
    if (context.state.phase === 'combat') {
      confidence += 0.1;
    }

    // Length confidence (longer text typically contains more intent)
    if (text.length > 20) confidence += 0.1;
    if (text.length > 50) confidence += 0.1;

    // Emotional clarity
    const emotionalTone = this.analyzeEmotionalTone(text);
    const emotionalIntensity = Math.max(
      emotionalTone.anger,
      emotionalTone.confidence,
      emotionalTone.fear,
      emotionalTone.humor,
      emotionalTone.seriousness,
      emotionalTone.desperation
    );
    confidence += emotionalIntensity * 0.2;

    return Math.min(1, confidence);
  }

  /**
   * Calculate strategic value of the dialogue
   */
  private calculateStrategicValue(
    intentType: DialogueIntent['type'],
    emotionalTone: EmotionalTone,
    context: CombatContext
  ): number {
    let value = 0.5; // Base value

    // Intent type value
    const intentValues = {
      coordinate: 0.9,
      intimidate: 0.8,
      deceive: 0.7,
      attack: 0.6,
      spell: 0.6,
      defend: 0.5,
      taunt: 0.4,
      persuade: 0.4,
      buff: 0.3,
      debuff: 0.3
    };

    value += intentValues[intentType] * 0.3;

    // Emotional impact on value
    value += (emotionalTone.confidence + emotionalTone.anger + emotionalTone.desperation) * 0.2;

    // Contextual value
    if (context.state.morale.allies < 0.5 && intentType === 'inspire') {
      value += 0.3;
    }

    if (context.state.morale.enemies > 0.7 && intentType === 'intimidate') {
      value += 0.3;
    }

    return Math.min(1, value);
  }

  /**
   * Generate mechanical effects from dialogue intent
   */
  private generateMechanics(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): DialogueMechanics {
    const combatAction = this.createCombatAction(intent, character);
    const bonuses = this.generateMechanicalBonuses(intent, character);
    const resourceCosts = this.calculateResourceCosts(combatAction, character);
    const duration = this.calculateEffectDuration(intent);
    const conditions = this.determineConditions(intent, context);
    const synergies = this.identifySynergies(intent, character, context);

    return {
      combatAction,
      bonuses,
      resourceCosts,
      duration,
      conditions,
      synergies
    };
  }

  /**
   * Create combat action from intent
   */
  private createCombatAction(intent: DialogueIntent, character: Character): CombatAction {
    const mapping = ACTION_MAPPINGS[intent.type] || ACTION_MAPPINGS.attack;

    const action: CombatAction = {
      type: mapping.primary as CombatAction['type'],
      actionName: intent.action || `${intent.type}_action`,
    };

    // Add action-specific properties
    if (intent.type === 'attack' || intent.type === 'spell') {
      const damageType = this.extractDamageType(intent.flavor || '');
      action.damage = {
        amount: this.calculateBaseDamage(character, intent),
        type: damageType,
        bonus: this.calculateDamageBonus(character, intent),
        critical: Math.random() < 0.05 // 5% chance for dialogue-triggered critical
      };
    }

    if (intent.type === 'intimidate' || intent.type === 'taunt') {
      action.save = {
        ability: 'wisdom',
        dc: this.calculateSaveDC(character, intent),
        effectOnFail: intent.type === 'intimidate' ? 'Frightened' : 'Disadvantage on next attack',
        effectOnSuccess: 'No effect'
      };
    }

    if (intent.type === 'buff' || intent.type === 'coordinate') {
      action.effect = {
        name: 'Dialogue Buff',
        duration: 3,
        description: `${intent.type} effect from dialogue`
      };
    }

    return action;
  }

  /**
   * Extract damage type from flavor text
   */
  private extractDamageType(text: string): string {
    const lowerText = text.toLowerCase();

    for (const [damageType, keywords] of Object.entries(DIALOGUE_DAMAGE_TYPES)) {
      for (const keyword of keywords) {
        if (lowerText.includes(keyword)) {
          return damageType;
        }
      }
    }

    return 'bludgeoning'; // Default damage type
  }

  /**
   * Calculate base damage from character stats and intent
   */
  private calculateBaseDamage(character: Character, intent: DialogueIntent): number {
    let baseDamage = 4; // Minimum damage

    // Add relevant ability modifier
    switch (intent.type) {
      case 'attack':
        baseDamage += Math.floor((character.abilities.strength - 10) / 2);
        break;
      case 'spell':
        baseDamage += Math.floor((character.abilities.intelligence - 10) / 2);
        break;
      case 'intimidate':
        baseDamage += Math.floor((character.abilities.charisma - 10) / 2);
        break;
    }

    // Add bonus from emotional intensity
    const emotionalBonus = Math.max(
      intent.emotionalTone.anger,
      intent.emotionalTone.confidence,
      intent.emotionalTone.desperation
    );
    baseDamage += Math.floor(emotionalBonus * 4);

    return Math.max(1, baseDamage);
  }

  /**
   * Calculate damage bonus from dialogue quality
   */
  private calculateDamageBonus(character: Character, intent: DialogueIntent): number {
    let bonus = 0;

    // Strategic value bonus
    bonus += Math.floor(intent.strategicValue * 3);

    // Confidence bonus
    bonus += Math.floor(intent.emotionalTone.confidence * 2);

    // Character skill bonus
    if (intent.type === 'intimidate') {
      bonus += character.skills.intimidation;
    }
    if (intent.type === 'persuade') {
      bonus += character.skills.persuasion;
    }

    return Math.floor(bonus);
  }

  /**
   * Calculate save DC for dialogue-based effects
   */
  private calculateSaveDC(character: Character, intent: DialogueIntent): number {
    const baseDC = 8;
    const proficiencyBonus = Math.floor((character.level - 1) / 4) + 2;
    const abilityModifier = Math.floor((character.abilities.charisma - 10) / 2);
    const confidenceBonus = Math.floor(intent.emotionalTone.confidence * 4);

    return baseDC + proficiencyBonus + abilityModifier + confidenceBonus;
  }

  /**
   * Generate mechanical bonuses from dialogue
   */
  private generateMechanicalBonuses(intent: DialogueIntent, character: Character): MechanicalBonus[] {
    const bonuses: MechanicalBonus[] = [];

    // Get base bonuses from dialogue type
    const dialogueBonuses = DIALOGUE_BONUSES[intent.type];
    if (dialogueBonuses) {
      if (dialogueBonuses.advantage) {
        bonuses.push({
          type: 'advantage',
          value: 1,
          source: `${intent.type}_dialogue`,
          appliesTo: dialogueBonuses.advantage,
          duration: dialogueBonuses.duration
        });
      }

      if (dialogueBonuses.bonus) {
        bonuses.push({
          ...dialogueBonuses.bonus,
          source: `${intent.type}_dialogue`,
          duration: dialogueBonuses.duration
        });
      }

      if (dialogueBonuses.inspiration) {
        bonuses.push({
          type: 'inspiration',
          value: 1,
          source: 'inspiring_dialogue',
          appliesTo: ['all'],
          duration: 0
        });
      }
    }

    // Add strategic value bonus
    if (intent.strategicValue > 0.7) {
      bonuses.push({
        type: 'bonus',
        value: Math.floor(intent.strategicTone * 2),
        source: 'strategic_dialogue',
        appliesTo: ['all_checks'],
        duration: 1
      });
    }

    return bonuses;
  }

  /**
   * Calculate resource costs for the action
   */
  private calculateResourceCosts(action: CombatAction, character: Character): ResourceCost[] {
    const costs: ResourceCost[] = [];

    // Base action cost
    costs.push({
      type: 'action',
      amount: 1
    });

    // Spell-specific costs
    if (action.type === 'spell_cast') {
      costs.push({
        type: 'spell_slot',
        amount: 1
      });
    }

    // Bonus actions for certain dialogue types
    if (action.actionName?.includes('taunt') || action.actionName?.includes('inspire')) {
      costs[0].type = 'bonus_action';
    }

    return costs;
  }

  /**
   * Calculate effect duration
   */
  private calculateEffectDuration(intent: DialogueIntent): number {
    let baseDuration = 1;

    // Longer based on strategic value
    baseDuration += Math.floor(intent.strategicValue * 2);

    // Extended by confidence
    baseDuration += Math.floor(intent.emotionalTone.confidence);

    return Math.min(10, baseDuration);
  }

  /**
   * Determine conditions applied by dialogue
   */
  private determineConditions(intent: DialogueIntent, context: CombatContext): string[] {
    const conditions: string[] = [];

    if (intent.type === 'intimidate' && intent.emotionalTone.confidence > 0.6) {
      conditions.push('Frightened');
    }

    if (intent.type === 'taunt' && intent.emotionalTone.humor > 0.5) {
      conditions.push('Rattled');
    }

    if (intent.type === 'deceive' && intent.confidence > 0.7) {
      conditions.push('Deceived');
    }

    return conditions;
  }

  /**
   * Identify synergies with other characters/actions
   */
  private identifySynergies(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): string[] {
    const synergies: string[] = [];

    if (intent.type === 'coordinate') {
      synergies.push('teamwork_bonus');
    }

    // Check for character-specific synergies
    for (const otherCharacter of context.characters) {
      if (otherCharacter.id === character.id) continue;

      // Paladin + Cleric synergy
      if (character.class.includes('Paladin') && otherCharacter.class.includes('Cleric')) {
        synergies.push('divine_synergy');
      }

      // Rogue + Ranger synergy
      if (character.class.includes('Rogue') && otherCharacter.class.includes('Ranger')) {
        synergies.push('skirmish_synergy');
      }

      // Wizard + Sorcerer synergy
      if (character.class.includes('Wizard') && otherCharacter.class.includes('Sorcerer')) {
        synergies.push('arcane_synergy');
      }
    }

    return synergies;
  }

  /**
   * Initialize character cache for quick lookups
   */
  private initializeCharacterCache(): void {
    for (const character of this.context.characters) {
      this.characterCache.set(character.id, character);
    }
  }

  /**
   * Generate unique dialogue ID
   */
  private generateDialogueId(): string {
    return `dialogue_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Batch process multiple dialogues
   */
  public batchProcess(
    dialogues: Array<{ characterId: string; text: string }>
  ): CombatDialogue[] {
    return dialogues.map(({ characterId, text }) =>
      this.parseDialogue(characterId, text, this.context)
    );
  }

  /**
   * Update context and reinitialize cache
   */
  public updateContext(newContext: CombatContext): void {
    this.context = newContext;
    this.initializeCharacterCache();
    this.intentCache.clear();
  }

  /**
   * Get intent history for a character
   */
  public getIntentHistory(characterId: string): DialogueIntent[] {
    return this.intentCache.get(characterId) || [];
  }

  /**
   * Cache intent for history tracking
   */
  private cacheIntent(characterId: string, intent: DialogueIntent): void {
    if (!this.intentCache.has(characterId)) {
      this.intentCache.set(characterId, []);
    }

    const history = this.intentCache.get(characterId)!;
    history.push(intent);

    // Keep only last 10 intents
    if (history.length > 10) {
      history.shift();
    }
  }
}