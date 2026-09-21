/**
 * AI Dialogue Enhancement Module
 * Real-time dialogue polishing, character voice preservation, and tactical suggestions
 */

import {
  Character,
  DialogueIntent,
  AIDialogueEnhancement,
  DialogueChange,
  TacticalCommunication,
  Personality,
  VoicePattern,
  EmotionalTone,
  CombatContext
} from '../types';
import { AI_ENHANCEMENT_SETTINGS, VOICE_PATTERNS, TACTICAL_PATTERNS } from '../utils/constants';

export class DialogueEnhancement {
  private characterProfiles: Map<string, CharacterProfile> = new Map();
  private contextualMemory: Map<string, DialogueContext[]> = new Map();
  private enhancementHistory: AIDialogueEnhancement[] = [];
  private tacticalSuggestions: TacticalSuggestion[] = [];

  constructor() {
    this.initializeCharacterProfiles();
  }

  /**
   * Enhance dialogue text with AI-powered improvements
   */
  public async enhanceDialogue(
    originalText: string,
    character: Character,
    intent: DialogueIntent,
    context: CombatContext
  ): Promise<AIDialogueEnhancement> {
    // Analyze original text
    const analysis = this.analyzeOriginalText(originalText, character, intent);

    // Generate enhanced versions
    const enhancedText = await this.generateEnhancedText(originalText, character, intent, context);

    // Create dialogue changes
    const changes = this.identifyChanges(originalText, enhancedText, character, intent);

    // Calculate quality metrics
    const quality = this.calculateQuality(enhancedText, changes, intent);
    const characterMatch = this.calculateCharacterMatch(enhancedText, character);

    const enhancement: AIDialogueEnhancement = {
      originalText,
      enhancedText,
      changes,
      quality,
      characterMatch
    };

    // Store enhancement for learning
    this.enhancementHistory.push(enhancement);
    this.updateContextualMemory(character.id, originalText, enhancedText, intent);

    return enhancement;
  }

  /**
   * Generate tactical communication suggestions
   */
  public async generateTacticalSuggestions(
    character: Character,
    context: CombatContext,
    currentSituation: string
  ): Promise<TacticalSuggestion[]> {
    const suggestions: TacticalSuggestion[] = [];

    // Analyze combat situation
    const situationAnalysis = this.analyzeCombatSituation(character, context, currentSituation);

    // Generate coordination suggestions
    if (this.shouldCoordinate(character, context)) {
      suggestions.push(...this.generateCoordinationSuggestions(character, context, situationAnalysis));
    }

    // Generate defensive suggestions
    if (this.shouldDefend(character, context)) {
      suggestions.push(...this.generateDefensiveSuggestions(character, context, situationAnalysis));
    }

    // Generate offensive suggestions
    if (this.shouldAttack(character, context)) {
      suggestions.push(...this.generateOffensiveSuggestions(character, context, situationAnalysis));
    }

    // Generate morale suggestions
    if (this.shouldBoostMorale(character, context)) {
      suggestions.push(...this.generateMoraleSuggestions(character, context, situationAnalysis));
    }

    return this.rankSuggestionsByPriority(suggestions, character, context);
  }

  /**
   * Generate real-time dialogue suggestions during combat
   */
  public async generateCombatDialogueSuggestions(
    character: Character,
    context: CombatContext,
    triggerEvent: string
  ): Promise<DialogueSuggestion[]> {
    const suggestions: DialogueSuggestion[] = [];

    // Character-specific response patterns
    const characterProfile = this.characterProfiles.get(character.id);
    if (!characterProfile) return suggestions;

    // Generate suggestions based on trigger
    switch (triggerEvent) {
      case 'ally_hit':
        suggestions.push(...this.generateSupportDialogue(character, characterProfile));
        break;
      case 'enemy_critical':
        suggestions.push(...this.generateIntimidationDialogue(character, characterProfile));
        break;
      case 'low_health':
        suggestions.push(...this.generateDesperationDialogue(character, characterProfile));
        break;
      case 'victory_near':
        suggestions.push(...this.generateVictoryDialogue(character, characterProfile));
        break;
      case 'team_coordination':
        suggestions.push(...this.generateCoordinationDialogue(character, characterProfile));
        break;
      default:
        suggestions.push(...this.generateGeneralDialogue(character, characterProfile, context));
    }

    return this.filterAppropriateSuggestions(suggestions, character, context);
  }

  /**
   * Apply emotional expression to dialogue
   */
  public applyEmotionalExpression(
    text: string,
    emotionalTone: EmotionalTone,
    intensity: number = 0.5
  ): string {
    let modifiedText = text;

    // Apply emotional modifiers based on dominant emotion
    const dominantEmotion = this.getDominantEmotion(emotionalTone);

    switch (dominantEmotion) {
      case 'anger':
        modifiedText = this.applyAngerModifiers(modifiedText, emotionalTone.anger, intensity);
        break;
      case 'confidence':
        modifiedText = this.applyConfidenceModifiers(modifiedText, emotionalTone.confidence, intensity);
        break;
      case 'fear':
        modifiedText = this.applyFearModifiers(modifiedText, emotionalTone.fear, intensity);
        break;
      case 'humor':
        modifiedText = this.applyHumorModifiers(modifiedText, emotionalTone.humor, intensity);
        break;
      case 'desperation':
        modifiedText = this.applyDesperationModifiers(modifiedText, emotionalTone.desperation, intensity);
        break;
    }

    return modifiedText;
  }

  /**
   * Generate battle cries and powerful combat phrases
   */
  public generateBattleCry(
    character: Character,
    combatSituation: string,
    emotionalState: EmotionalTone
  ): string {
    const profile = this.characterProfiles.get(character.id);
    if (!profile) return this.generateGenericBattleCry();

    const templates = this.getBattleCryTemplates(character.class, emotionalState);
    const template = templates[Math.floor(Math.random() * templates.length)];

    return this.fillBattleCryTemplate(template, character, combatSituation, emotionalState);
  }

  /**
   * Create character-appropriate speech patterns
   */
  public adaptToCharacterVoice(
    text: string,
    character: Character,
    voicePattern?: VoicePattern
  ): string {
    const pattern = voicePattern || character.voice;
    let adaptedText = text;

    // Apply vocabulary adjustments
    adaptedText = this.applyVocabularyStyle(adaptedText, pattern.vocabulary);

    // Apply sentence structure
    adaptedText = this.applySentenceStructure(adaptedText, pattern.sentenceStructure);

    // Add character-specific phrases and tics
    adaptedText = this.addCharacterPhrases(adaptedText, pattern.commonPhrases);
    adaptedText = this.addCharacterTics(adaptedText, pattern.tics);

    return adaptedText;
  }

  // Private implementation methods

  private analyzeOriginalText(text: string, character: Character, intent: DialogueIntent): TextAnalysis {
    return {
      length: text.length,
      complexity: this.calculateComplexity(text),
      emotionalClarity: this.calculateEmotionalClarity(text, intent.emotionalTone),
      tacticalValue: this.calculateTacticalValue(text, intent),
      characterConsistency: this.calculateCharacterConsistency(text, character)
    };
  }

  private async generateEnhancedText(
    originalText: string,
    character: Character,
    intent: DialogueIntent,
    context: CombatContext
  ): Promise<string> {
    let enhancedText = originalText;

    // Apply character voice consistency
    enhancedText = this.adaptToCharacterVoice(enhancedText, character);

    // Enhance emotional expression
    enhancedText = this.applyEmotionalExpression(enhancedText, intent.emotionalTone);

    // Add tactical context
    enhancedText = this.addTacticalContext(enhancedText, intent, context);

    // Optimize for combat clarity
    enhancedText = this.optimizeForCombat(enhancedText, intent);

    // Ensure within acceptable length limits
    enhancedText = this.adjustLength(enhancedText, originalText.length);

    return enhancedText;
  }

  private identifyChanges(
    original: string,
    enhanced: string,
    character: Character,
    intent: DialogueIntent
  ): DialogueChange[] {
    const changes: DialogueChange[] = [];

    // Compare word by word to identify changes
    const originalWords = original.split(' ');
    const enhancedWords = enhanced.split(' ');

    // Find additions, deletions, and modifications
    const diff = this.calculateTextDiff(originalWords, enhancedWords);

    for (const change of diff) {
      changes.push({
        type: this.categorizeChange(change, character, intent),
        original: change.original,
        modified: change.modified,
        reason: change.reason
      });
    }

    return changes.slice(0, AI_ENHANCEMENT_SETTINGS.maxChanges);
  }

  private calculateQuality(enhancedText: string, changes: DialogueChange[], intent: DialogueIntent): number {
    let quality = 0.5; // Base quality

    // Clarity scoring
    quality += this.calculateClarityScore(enhancedText) * 0.3;

    // Tactical relevance
    quality += this.calculateTacticalRelevance(enhancedText, intent) * 0.2;

    // Character consistency
    quality += this.calculateConsistencyScore(enhancedText, changes) * 0.2;

    // Emotional impact
    quality += this.calculateEmotionalImpact(enhancedText) * 0.2;

    // Length appropriateness
    quality += this.calculateLengthScore(enhancedText) * 0.1;

    return Math.min(1, Math.max(0, quality));
  }

  private calculateCharacterMatch(enhancedText: string, character: Character): number {
    const profile = this.characterProfiles.get(character.id);
    if (!profile) return 0.5;

    let match = 0.5;

    // Vocabulary match
    match += this.calculateVocabularyMatch(enhancedText, profile.vocabulary) * 0.3;

    // Sentence structure match
    match += this.calculateStructureMatch(enhancedText, profile.sentencePatterns) * 0.2;

    // Personality trait match
    match += this.calculatePersonalityMatch(enhancedText, character.personality) * 0.3;

    // Common phrase usage
    match += this.calculatePhraseMatch(enhancedText, character.voice.commonPhrases) * 0.2;

    return Math.min(1, Math.max(0, match));
  }

  private analyzeCombatSituation(
    character: Character,
    context: CombatContext,
    currentSituation: string
  ): SituationAnalysis {
    return {
      threatLevel: this.calculateThreatLevel(character, context),
      opportunityLevel: this.calculateOpportunityLevel(character, context),
      teamCohesion: this.calculateTeamCohesion(character, context),
      environmentalFactors: this.analyzeEnvironmentalFactors(context),
      timingCriticality: this.calculateTimingCriticality(character, context)
    };
  }

  private generateCoordinationSuggestions(
    character: Character,
    context: CombatContext,
    analysis: SituationAnalysis
  ): TacticalSuggestion[] {
    const suggestions: TacticalSuggestion[] = [];

    const coordinationPatterns = TACTICAL_PATTERNS.coordinate;
    const allies = this.getAllies(character, context);

    for (const pattern of coordinationPatterns) {
      const suggestion: TacticalSuggestion = {
        type: 'coordinate',
        text: this.generateCoordinationText(pattern, character, allies, context),
        priority: this.calculateCoordinationPriority(pattern, analysis),
        expectedOutcome: this.predictCoordinationOutcome(pattern, character, allies),
        timing: 'immediate'
      };
      suggestions.push(suggestion);
    }

    return suggestions;
  }

  private generateDefensiveSuggestions(
    character: Character,
    context: CombatContext,
    analysis: SituationAnalysis
  ): TacticalSuggestion[] {
    const suggestions: TacticalSuggestion[] = [];

    if (character.hp < character.maxHp * 0.3) {
      suggestions.push({
        type: 'defend',
        text: this.generateDefensiveDialogue(character, context),
        priority: 'high',
        expectedOutcome: 'Reduces incoming damage by 50%',
        timing: 'immediate'
      });
    }

    return suggestions;
  }

  private generateOffensiveSuggestions(
    character: Character,
    context: CombatContext,
    analysis: SituationAnalysis
  ): TacticalSuggestion[] {
    const suggestions: TacticalSuggestion[] = [];

    if (analysis.opportunityLevel > 0.7) {
      suggestions.push({
        type: 'attack',
        text: this.generateOffensiveDialogue(character, context),
        priority: 'high',
        expectedOutcome: '+2 to attack and damage rolls',
        timing: 'immediate'
      });
    }

    return suggestions;
  }

  private generateMoraleSuggestions(
    character: Character,
    context: CombatContext,
    analysis: SituationAnalysis
  ): TacticalSuggestion[] {
    const suggestions: TacticalSuggestion[] = [];

    if (analysis.teamCohesion < 0.5) {
      suggestions.push({
        type: 'inspire',
        text: this.generateMoraleDialogue(character, context),
        priority: 'medium',
        expectedOutcome: 'Allies gain advantage on next save',
        timing: 'bonus_action'
      });
    }

    return suggestions;
  }

  // Text modification methods

  private applyAngerModifiers(text: string, angerLevel: number, intensity: number): string {
    if (angerLevel < 0.5) return text;

    const angryWords = ['DAMN', 'CURSE', 'DESTROY', 'CRUSH', 'ANNIHILATE'];
    const exclamationMultiplier = Math.floor(angerLevel * 3) + 1;

    let modifiedText = text.toUpperCase();

    // Add appropriate number of exclamation marks
    if (modifiedText.endsWith('!')) {
      modifiedText = modifiedText.slice(0, -1) + '!'.repeat(exclamationMultiplier);
    } else {
      modifiedText += '!';
    }

    return modifiedText;
  }

  private applyConfidenceModifiers(text: string, confidenceLevel: number, intensity: number): string {
    if (confidenceLevel < 0.6) return text;

    const confidentPrefixes = ['Behold', 'Witness', 'Observe', 'Mark my words'];
    const confidentSuffixes = ['as intended', 'without doubt', 'with certainty'];

    const prefix = confidentPrefixes[Math.floor(Math.random() * confidentPrefixes.length)];
    const suffix = confidentSuffixes[Math.floor(Math.random() * confidentSuffixes.length)];

    return `${prefix}, ${text}, ${suffix}!`;
  }

  private applyFearModifiers(text: string, fearLevel: number, intensity: number): string {
    if (fearLevel < 0.5) return text;

    const fearfulWords = ['please', 'mercy', 'spare', 'help', 'run'];
    const stutterPattern = fearLevel > 0.7 ? 'w-w-' : '';

    return `${stutterPattern}${text.toLowerCase()}, ${fearfulWords[Math.floor(Math.random() * fearfulWords.length)]}!`;
  }

  private applyHumorModifiers(text: string, humorLevel: number, intensity: number): string {
    if (humorLevel < 0.5) return text;

    const wittyEndings = ['...or so they think!', '...the irony!', '...how amusing!', '...classic!'];
    const ending = wittyEndings[Math.floor(Math.random() * wittyEndings.length)];

    return `${text} ${ending}`;
  }

  private applyDesperationModifiers(text: string, desperationLevel: number, intensity: number): string {
    if (desperationLevel < 0.6) return text;

    const desperateWords = ['MUST', 'HAVE TO', 'NEED TO', 'PLEASE'];
    const desperate = desperateWords[Math.floor(Math.random() * desperateWords.length)];

    return `${desperate} ${text.toUpperCase()}!`;
  }

  // Helper methods

  private getDominantEmotion(emotionalTone: EmotionalTone): keyof EmotionalTone {
    return Object.entries(emotionalTone).reduce((a, b) =>
      emotionalTone[a[0] as keyof EmotionalTone] > emotionalTone[b[0] as keyof EmotionalTone] ? a : b
    )[0] as keyof EmotionalTone;
  }

  private calculateComplexity(text: string): number {
    const words = text.split(' ');
    const avgWordLength = words.reduce((sum, word) => sum + word.length, 0) / words.length;
    const sentences = text.split(/[.!?]+/).length;

    return (avgWordLength / 10 + words.length / 50 + sentences / 10) / 3;
  }

  private calculateEmotionalClarity(text: string, emotionalTone: EmotionalTone): number {
    const maxEmotion = Math.max(...Object.values(emotionalTone));
    const clarity = maxEmotion > 0.7 ? 1 : maxEmotion / 0.7;
    return clarity;
  }

  private calculateTacticalValue(text: string, intent: DialogueIntent): number {
    return intent.strategicValue || 0.5;
  }

  private calculateCharacterConsistency(text: string, character: Character): number {
    // Simplified consistency check
    return 0.7;
  }

  private calculateTextDiff(original: string[], enhanced: string[]): TextDiff[] {
    // Simplified diff calculation
    return [{
      original: original.join(' '),
      modified: enhanced.join(' '),
      reason: 'Enhancement'
    }];
  }

  private categorizeChange(change: TextDiff, character: Character, intent: DialogueIntent): DialogueChange['type'] {
    if (change.modified.includes('!') && !change.original.includes('!')) {
      return 'emotion';
    }
    if (change.modified.length > change.original.length * 1.2) {
      return 'flavor';
    }
    return 'wording';
  }

  private adjustLength(text: string, originalLength: number): string {
    const maxLength = originalLength * AI_ENHANCEMENT_SETTINGS.maxLengthIncrease;
    const minLength = originalLength * AI_ENHANCEMENT_SETTINGS.maxLengthDecrease;

    if (text.length > maxLength) {
      return text.substring(0, Math.floor(maxLength));
    }
    if (text.length < minLength && originalLength > 10) {
      // Add minimal filler if too short
      return text + '!';
    }

    return text;
  }

  private getAllies(character: Character, context: CombatContext): Character[] {
    return context.characters.filter(c => c.id !== character.id);
  }

  private initializeCharacterProfiles(): void {
    // Initialize with default profiles
    // This would be populated with character-specific data
  }

  private updateContextualMemory(characterId: string, original: string, enhanced: string, intent: DialogueIntent): void {
    if (!this.contextualMemory.has(characterId)) {
      this.contextualMemory.set(characterId, []);
    }

    const memory = this.contextualMemory.get(characterId)!;
    memory.push({
      original,
      enhanced,
      intent,
      timestamp: new Date()
    });

    // Keep only last 20 entries
    if (memory.length > 20) {
      memory.shift();
    }
  }

  // Placeholder implementations for missing methods
  private generateSupportDialogue(character: Character, profile: CharacterProfile): DialogueSuggestion[] {
    return [];
  }

  private generateIntimidationDialogue(character: Character, profile: CharacterProfile): DialogueSuggestion[] {
    return [];
  }

  private generateDesperationDialogue(character: Character, profile: CharacterProfile): DialogueSuggestion[] {
    return [];
  }

  private generateVictoryDialogue(character: Character, profile: CharacterProfile): DialogueSuggestion[] {
    return [];
  }

  private generateCoordinationDialogue(character: Character, profile: CharacterProfile): DialogueSuggestion[] {
    return [];
  }

  private generateGeneralDialogue(character: Character, profile: CharacterProfile, context: CombatContext): DialogueSuggestion[] {
    return [];
  }

  private filterAppropriateSuggestions(suggestions: DialogueSuggestion[], character: Character, context: CombatContext): DialogueSuggestion[] {
    return suggestions;
  }

  private rankSuggestionsByPriority(suggestions: TacticalSuggestion[], character: Character, context: CombatContext): TacticalSuggestion[] {
    return suggestions.sort((a, b) => this.getPriorityValue(b.priority) - this.getPriorityValue(a.priority));
  }

  private getPriorityValue(priority: string | number): number {
    if (typeof priority === 'number') return priority;
    const priorityMap = { low: 1, medium: 2, high: 3, critical: 4 };
    return priorityMap[priority as keyof typeof priorityMap] || 1;
  }

  private shouldCoordinate(character: Character, context: CombatContext): boolean {
    return context.characters.length > 2;
  }

  private shouldDefend(character: Character, context: CombatContext): boolean {
    return character.hp < character.maxHp * 0.5;
  }

  private shouldAttack(character: Character, context: CombatContext): boolean {
    return character.hp > character.maxHp * 0.7;
  }

  private shouldBoostMorale(character: Character, context: CombatContext): boolean {
    return character.level >= 5; // Higher level characters can boost morale
  }

  private calculateThreatLevel(character: Character, context: CombatContext): number {
    return 0.5; // Placeholder
  }

  private calculateOpportunityLevel(character: Character, context: CombatContext): number {
    return 0.5; // Placeholder
  }

  private calculateTeamCohesion(character: Character, context: CombatContext): number {
    return 0.5; // Placeholder
  }

  private analyzeEnvironmentalFactors(context: CombatContext): any {
    return {}; // Placeholder
  }

  private calculateTimingCriticality(character: Character, context: CombatContext): number {
    return 0.5; // Placeholder
  }

  private generateCoordinationText(pattern: string, character: Character, allies: Character[], context: CombatContext): string {
    return pattern; // Placeholder
  }

  private calculateCoordinationPriority(pattern: string, analysis: SituationAnalysis): string | number {
    return 'medium'; // Placeholder
  }

  private predictCoordinationOutcome(pattern: string, character: Character, allies: Character[]): string {
    return 'Improved team coordination'; // Placeholder
  }

  private generateDefensiveDialogue(character: Character, context: CombatContext): string {
    return 'I must defend myself!'; // Placeholder
  }

  private generateOffensiveDialogue(character: Character, context: CombatContext): string {
    return 'Attack now!'; // Placeholder
  }

  private generateMoraleDialogue(character: Character, context: CombatContext): string {
    return 'Stay strong, allies!'; // Placeholder
  }

  // Additional helper methods
  private calculateClarityScore(text: string): number { return 0.7; }
  private calculateTacticalRelevance(text: string, intent: DialogueIntent): number { return 0.7; }
  private calculateConsistencyScore(text: string, changes: DialogueChange[]): number { return 0.7; }
  private calculateEmotionalImpact(text: string): number { return 0.7; }
  private calculateLengthScore(text: string): number { return 0.7; }
  private calculateVocabularyMatch(text: string, vocabulary: string[]): number { return 0.7; }
  private calculateStructureMatch(text: string, patterns: string[]): number { return 0.7; }
  private calculatePersonalityMatch(text: string, personality: Personality): number { return 0.7; }
  private calculatePhraseMatch(text: string, phrases: string[]): number { return 0.7; }
  private applyVocabularyStyle(text: string, style: string): string { return text; }
  private applySentenceStructure(text: string, structure: string): string { return text; }
  private addCharacterPhrases(text: string, phrases: string[]): string { return text; }
  private addCharacterTics(text: string, tics: string[]): string { return text; }
  private addTacticalContext(text: string, intent: DialogueIntent, context: CombatContext): string { return text; }
  private optimizeForCombat(text: string, intent: DialogueIntent): string { return text; }
  private getBattleCryTemplates(characterClass: string, emotionalState: EmotionalTone): string[] { return []; }
  private fillBattleCryTemplate(template: string, character: Character, situation: string, emotionalState: EmotionalTone): string { return template; }
  private generateGenericBattleCry(): string { return 'For victory!'; }
}

interface CharacterProfile {
  vocabulary: string[];
  sentencePatterns: string[];
  personalityTraits: string[];
  commonPhrases: string[];
  speechTics: string[];
}

interface DialogueContext {
  original: string;
  enhanced: string;
  intent: DialogueIntent;
  timestamp: Date;
}

interface TextAnalysis {
  length: number;
  complexity: number;
  emotionalClarity: number;
  tacticalValue: number;
  characterConsistency: number;
}

interface TextDiff {
  original: string;
  modified: string;
  reason: string;
}

interface SituationAnalysis {
  threatLevel: number;
  opportunityLevel: number;
  teamCohesion: number;
  environmentalFactors: any;
  timingCriticality: number;
}

interface TacticalSuggestion {
  type: string;
  text: string;
  priority: string | number;
  expectedOutcome: string;
  timing: string;
}

interface DialogueSuggestion {
  type: string;
  text: string;
  context: string;
  priority: string;
}