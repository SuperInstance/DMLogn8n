/**
 * Conversational Combat System - Main Orchestrator
 * Revolutionary system that transforms dialogue into gameplay mechanics
 */

import {
  CombatDialogue,
  DialogueMechanics,
  CombatContext,
  Character,
  CombatEvent,
  NarrativeElement,
  AIDialogueEnhancement,
  TacticalSuggestion,
  ConversationFlow
} from '../types';
import { DEFAULT_CONFIG } from '../utils/constants';

import { DialogueToActionParser } from '../parsers/dialogue-to-action-parser';
import { StrategicDialogueMechanics } from '../mechanics/strategic-dialogue-mechanics';
import { CombatNarrativeEngine } from '../narrative/combat-narrative-engine';
import { DialogueCombatIntegration } from '../integration/dialogue-combat-integration';
import { DialogueEnhancement } from '../ai/dialogue-enhancement';

export class ConversationalCombatSystem {
  private dialogueParser: DialogueToActionParser;
  private strategicMechanics: StrategicDialogueMechanics;
  private narrativeEngine: CombatNarrativeEngine;
  private combatIntegration: DialogueCombatIntegration;
  private dialogueEnhancement: DialogueEnhancement;

  private combatContext: CombatContext;
  private currentConversations: Map<string, ConversationFlow> = new Map();
  private eventHistory: CombatEvent[] = [];
  private systemMetrics: SystemMetrics;
  private isInitialized: boolean = false;

  constructor(initialContext?: CombatContext, config?: any) {
    this.combatContext = initialContext || this.createDefaultContext();
    this.systemMetrics = this.initializeMetrics();

    // Initialize subsystems
    this.dialogueParser = new DialogueToActionParser(this.combatContext);
    this.strategicMechanics = new StrategicDialogueMechanics();
    this.narrativeEngine = new CombatNarrativeEngine();
    this.combatIntegration = new DialogueCombatIntegration(this.combatContext);
    this.dialogueEnhancement = new DialogueEnhancement();

    this.isInitialized = true;
  }

  /**
   * Main entry point - Process dialogue in combat
   */
  public async processDialogue(
    characterId: string,
    dialogueText: string,
    options?: DialogueProcessingOptions
  ): Promise<DialogueProcessingResult> {
    if (!this.isInitialized) {
      throw new Error('Conversational Combat System not initialized');
    }

    const startTime = Date.now();

    try {
      // Step 1: Parse dialogue and extract intent
      const combatDialogue = this.dialogueParser.parseDialogue(
        characterId,
        dialogueText,
        this.combatContext
      );

      // Step 2: Apply AI enhancement if enabled
      let enhancedDialogue = combatDialogue;
      if (options?.enableAIEnhancement !== false) {
        const enhancement = await this.dialogueEnhancement.enhanceDialogue(
          dialogueText,
          this.getCharacter(characterId),
          combatDialogue.intent!,
          this.combatContext
        );

        enhancedDialogue = {
          ...combatDialogue,
          text: enhancement.enhancedText
        };

        // Store enhancement for learning
        this.systemMetrics.enhancementsProcessed++;
      }

      // Step 3: Generate strategic mechanics
      const mechanics = this.strategicMechanics.processStrategicDialogue(
        enhancedDialogue.intent!,
        this.getCharacter(characterId),
        this.combatContext
      );

      // Step 4: Process through combat integration
      const combatEvents = await this.combatIntegration.processDialogueInCombat(
        enhancedDialogue,
        mechanics
      );

      // Step 5: Generate narrative elements
      const narrativeElements = this.narrativeEngine.generateCombatNarrative(
        enhancedDialogue,
        mechanics,
        this.combatContext
      );

      // Step 6: Combine events with narrative
      const enrichedEvents = this.enrichEventsWithNarrative(combatEvents, narrativeElements);

      // Step 7: Update conversation flow
      this.updateConversationFlow(characterId, enhancedDialogue, enrichedEvents);

      // Step 8: Update metrics
      const processingTime = Date.now() - startTime;
      this.updateMetrics(enhancedDialogue, mechanics, processingTime);

      // Step 9: Generate suggestions for next actions
      const suggestions = await this.generateSuggestions(characterId, enhancedDialogue);

      // Step 10: Return comprehensive result
      const result: DialogueProcessingResult = {
        originalDialogue: combatDialogue,
        enhancedDialogue,
        mechanics,
        events: enrichedEvents,
        narrative: narrativeElements,
        suggestions,
        metrics: this.getDialogueMetrics(processingTime),
        context: this.combatContext
      };

      // Store in event history
      this.eventHistory.push(...enrichedEvents);

      return result;

    } catch (error) {
      console.error('Error processing dialogue:', error);
      throw error;
    }
  }

  /**
   * Start a new conversation with multiple participants
   */
  public startConversation(participants: string[], topic?: string): ConversationSession {
    const sessionId = this.generateSessionId();
    const conversationFlow: ConversationFlow = {
      participants,
      currentSpeaker: participants[0],
      context: {
        topic: topic || 'combat_situation',
        tension: 0.5,
        urgency: 0.5,
        formality: 0.5,
        hostility: 0.3
      },
      history: [],
      pendingActions: []
    };

    this.currentConversations.set(sessionId, conversationFlow);

    return {
      sessionId,
      participants,
      isActive: true,
      context: conversationFlow.context
    };
  }

  /**
   * Get real-time tactical suggestions during combat
   */
  public async getTacticalSuggestions(
    characterId: string,
    situation?: string
  ): Promise<TacticalSuggestion[]> {
    const character = this.getCharacter(characterId);
    const currentSituation = situation || this.assessCurrentSituation(characterId);

    return this.dialogueEnhancement.generateTacticalSuggestions(
      character,
      this.combatContext,
      currentSituation
    );
  }

  /**
   * Generate dialogue suggestions based on combat events
   */
  public async getDialogueSuggestions(
    characterId: string,
    triggerEvent: string
  ): Promise<string[]> {
    const character = this.getCharacter(characterId);
    const suggestions = await this.dialogueEnhancement.generateCombatDialogueSuggestions(
      character,
      this.combatContext,
      triggerEvent
    );

    return suggestions.map(s => s.text);
  }

  /**
   * Get current combat state with dialogue integration
   */
  public getCombatState(): CombatStateReport {
    return {
      context: this.combatContext,
      activeConversations: Array.from(this.currentConversations.entries()).map(([id, flow]) => ({
        sessionId: id,
        participants: flow.participants,
        currentSpeaker: flow.currentSpeaker,
        context: flow.context,
        historyLength: flow.history.length
      })),
      eventSummary: {
        totalEvents: this.eventHistory.length,
        dialogueEvents: this.eventHistory.filter(e => e.type === 'dialogue').length,
        actionEvents: this.eventHistory.filter(e => e.type === 'action').length,
        effectEvents: this.eventHistory.filter(e => e.type === 'effect').length
      },
      systemMetrics: this.systemMetrics,
      combatIntensity: this.narrativeEngine.getCombatIntensity()
    };
  }

  /**
   * Update combat context (e.g., new round, character changes)
   */
  public updateCombatContext(newContext: Partial<CombatContext>): void {
    this.combatContext = { ...this.combatContext, ...newContext };

    // Update all subsystems
    this.dialogueParser.updateContext(this.combatContext);
    this.combatIntegration.updateCombatState(this.combatContext);

    this.systemMetrics.contextUpdates++;
  }

  /**
   * Generate spectator-friendly combat narrative
   */
  public generateSpectatorNarrative(timeframe?: NarrativeTimeframe): SpectatorNarrative {
    const events = this.filterEventsByTimeframe(this.eventHistory, timeframe);
    const narrative = this.narrativeEngine.getNarrativeHistory();

    return {
      summary: this.generateCombatSummary(events),
      keyMoments: this.extractKeyMoments(events),
      dialogueHighlights: this.extractDialogueHighlights(events),
      tacticalAnalysis: this.generateTacticalAnalysis(events),
      emotionalJourney: this.trackEmotionalJourney(events),
      timeline: this.createNarrativeTimeline(events, narrative)
    };
  }

  /**
   * Export combat data for analysis or replay
   */
  public exportCombatData(): CombatExportData {
    return {
      combatContext: this.combatContext,
      eventHistory: this.eventHistory,
      conversationHistory: Array.from(this.currentConversations.entries()),
      systemMetrics: this.systemMetrics,
      narrativeHistory: this.narrativeEngine.getNarrativeHistory(),
      enhancements: this.dialogueEnhancement['enhancementHistory'] || [],
      exportTimestamp: new Date(),
      version: '1.0.0'
    };
  }

  /**
   * Import combat data for replay or analysis
   */
  public importCombatData(data: CombatExportData): void {
    this.combatContext = data.combatContext;
    this.eventHistory = data.eventHistory;
    this.systemMetrics = data.systemMetrics;

    // Rebuild conversations
    this.currentConversations.clear();
    for (const [sessionId, flow] of data.conversationHistory) {
      this.currentConversations.set(sessionId, flow);
    }

    // Reinitialize subsystems with imported context
    this.dialogueParser.updateContext(this.combatContext);
    this.combatIntegration.updateCombatState(this.combatContext);
  }

  // Private helper methods

  private getCharacter(characterId: string): Character {
    const character = this.combatContext.characters.find(c => c.id === characterId);
    if (!character) {
      throw new Error(`Character ${characterId} not found in combat context`);
    }
    return character;
  }

  private enrichEventsWithNarrative(events: CombatEvent[], narrative: NarrativeElement[]): CombatEvent[] {
    return events.map(event => ({
      ...event,
      narrative: [...event.narrative, ...narrative.filter(n => this.shouldAttachNarrative(n, event))]
    }));
  }

  private shouldAttachNarrative(narrative: NarrativeElement, event: CombatEvent): boolean {
    // Simple matching logic - could be enhanced
    return narrative.type === 'description' || narrative.type === 'effect';
  }

  private updateConversationFlow(
    characterId: string,
    dialogue: CombatDialogue,
    events: CombatEvent[]
  ): void {
    // Find or create conversation for this character
    let conversation = Array.from(this.currentConversations.values())
      .find(conv => conv.participants.includes(characterId));

    if (!conversation) {
      // Create new conversation
      const sessionId = this.generateSessionId();
      conversation = this.startConversation([characterId]).context as any;
      this.currentConversations.set(sessionId, conversation);
    }

    // Update conversation context
    if (dialogue.intent) {
      conversation.context.tension = Math.min(1, conversation.context.tension + dialogue.intent.emotionalTone.anger * 0.1);
      conversation.context.urgency = Math.min(1, conversation.context.urgency + dialogue.intent.emotionalTone.desperation * 0.1);
    }

    // Add to history
    conversation.history.push({
      id: this.generateId(),
      speaker: characterId,
      text: dialogue.text,
      intent: dialogue.intent!,
      response: this.generateAutoResponse(dialogue, events),
      timestamp: new Date()
    });

    // Rotate speaker
    const currentIndex = conversation.participants.indexOf(characterId);
    conversation.currentSpeaker = conversation.participants[(currentIndex + 1) % conversation.participants.length];
  }

  private generateAutoResponse(dialogue: CombatDialogue, events: CombatEvent[]): string {
    // Simple auto-response generation
    if (dialogue.intent?.type === 'intimidate') {
      return 'The enemy appears intimidated by your words.';
    } else if (dialogue.intent?.type === 'coordinate') {
      return 'Your allies acknowledge your coordination.';
    }
    return 'Your words echo across the battlefield.';
  }

  private async generateSuggestions(characterId: string, dialogue: CombatDialogue): Promise<TacticalSuggestion[]> {
    const character = this.getCharacter(characterId);
    const situation = this.assessCurrentSituation(characterId);

    return this.dialogueEnhancement.generateTacticalSuggestions(
      character,
      this.combatContext,
      situation
    );
  }

  private assessCurrentSituation(characterId: string): string {
    const character = this.getCharacter(characterId);
    const allies = this.combatContext.characters.filter(c => c.id !== characterId);
    const enemies = this.combatContext.characters.filter(c => c.id === characterId); // Simplified

    if (character.hp < character.maxHp * 0.3) {
      return 'critical_injury';
    } else if (allies.length > enemies.length) {
      return 'numerical_advantage';
    } else if (this.combatState.state.phase === 'ending') {
      return 'combat_conclusion';
    }

    return 'standard_combat';
  }

  private updateMetrics(dialogue: CombatDialogue, mechanics: DialogueMechanics, processingTime: number): void {
    this.systemMetrics.dialoguesProcessed++;
    this.systemMetrics.totalProcessingTime += processingTime;
    this.systemMetrics.averageProcessingTime = this.systemMetrics.totalProcessingTime / this.systemMetrics.dialoguesProcessed;

    if (dialogue.intent?.strategicValue > 0.8) {
      this.systemMetrics.highValueDialogues++;
    }

    if (mechanics.bonuses.length > 2) {
      this.systemMetrics.complexMechanics++;
    }
  }

  private getDialogueMetrics(processingTime: number): DialogueMetrics {
    return {
      processingTime,
      intentConfidence: 0.8, // Placeholder
      strategicValue: 0.7, // Placeholder
      narrativeElementsGenerated: 3, // Placeholder
      mechanicalEffectsApplied: 2 // Placeholder
    };
  }

  private createDefaultContext(): CombatContext {
    return {
      round: 1,
      turn: 1,
      characters: [],
      environment: {
        name: 'Battlefield',
        description: 'A generic combat area',
        features: [],
        hazards: [],
        opportunities: []
      },
      state: {
        phase: 'combat',
        activeTurns: [],
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
    };
  }

  private initializeMetrics(): SystemMetrics {
    return {
      dialoguesProcessed: 0,
      enhancementsProcessed: 0,
      averageProcessingTime: 0,
      totalProcessingTime: 0,
      highValueDialogues: 0,
      complexMechanics: 0,
      contextUpdates: 0
    };
  }

  // ID generation
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateId(): string {
    return `id_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Spectator narrative helpers
  private filterEventsByTimeframe(events: CombatEvent[], timeframe?: NarrativeTimeframe): CombatEvent[] {
    if (!timeframe) return events;

    const now = new Date();
    const cutoff = new Date(now.getTime() - this.getTimeframeMs(timeframe));

    return events.filter(event => event.timestamp >= cutoff);
  }

  private getTimeframeMs(timeframe: NarrativeTimeframe): number {
    const multipliers = {
      'last_minute': 60000,
      'last_5_minutes': 300000,
      'last_round': 600000, // 10 minutes per round
      'entire_combat': 0
    };
    return multipliers[timeframe];
  }

  private generateCombatSummary(events: CombatEvent[]): string {
    const dialogueEvents = events.filter(e => e.type === 'dialogue').length;
    const actionEvents = events.filter(e => e.type === 'action').length;
    const effectEvents = events.filter(e => e.type === 'effect').length;

    return `Combat featured ${dialogueEvents} dialogue interactions, ${actionEvents} combat actions, and ${effectEvents} mechanical effects.`;
  }

  private extractKeyMoments(events: CombatEvent[]): string[] {
    return events
      .filter(e => e.narrative.some(n => n.cinematic))
      .map(e => e.narrative.find(n => n.cinematic)?.content || '')
      .filter(content => content.length > 0);
  }

  private extractDialogueHighlights(events: CombatEvent[]): string[] {
    return events
      .filter(e => e.type === 'dialogue')
      .map(e => e.data.dialogue?.text || '')
      .filter(text => text.length > 0);
  }

  private generateTacticalAnalysis(events: CombatEvent[]): string {
    // Analyze tactical patterns from events
    return 'Tactical analysis shows effective use of dialogue-driven mechanics and coordinated team strategies.';
  }

  private trackEmotionalJourney(events: CombatEvent[]): EmotionalJourneyPoint[] {
    // Extract emotional progression from dialogue events
    return [];
  }

  private createNarrativeTimeline(events: CombatEvent[], narrative: NarrativeElement[]): NarrativeTimelineEntry[] {
    return events.map(event => ({
      timestamp: event.timestamp,
      type: event.type,
      description: event.narrative[0]?.content || 'Combat action occurred',
      speaker: event.characterId ? this.getCharacter(event.characterId).name : undefined,
      cinematic: event.narrative.some(n => n.cinematic)
    }));
  }

  // Getters
  get combatState() {
    return this.combatContext;
  }

  get metrics() {
    return this.systemMetrics;
  }

  get history() {
    return this.eventHistory;
  }
}

// Type definitions for the main system

export interface DialogueProcessingOptions {
  enableAIEnhancement?: boolean;
  generateNarrative?: boolean;
  applyMechanics?: boolean;
  trackMetrics?: boolean;
}

export interface DialogueProcessingResult {
  originalDialogue: CombatDialogue;
  enhancedDialogue: CombatDialogue;
  mechanics: DialogueMechanics;
  events: CombatEvent[];
  narrative: NarrativeElement[];
  suggestions: TacticalSuggestion[];
  metrics: DialogueMetrics;
  context: CombatContext;
}

export interface DialogueMetrics {
  processingTime: number;
  intentConfidence: number;
  strategicValue: number;
  narrativeElementsGenerated: number;
  mechanicalEffectsApplied: number;
}

export interface ConversationSession {
  sessionId: string;
  participants: string[];
  isActive: boolean;
  context: any;
}

export interface CombatStateReport {
  context: CombatContext;
  activeConversations: Array<{
    sessionId: string;
    participants: string[];
    currentSpeaker: string;
    context: any;
    historyLength: number;
  }>;
  eventSummary: {
    totalEvents: number;
    dialogueEvents: number;
    actionEvents: number;
    effectEvents: number;
  };
  systemMetrics: SystemMetrics;
  combatIntensity: number;
}

export interface SpectatorNarrative {
  summary: string;
  keyMoments: string[];
  dialogueHighlights: string[];
  tacticalAnalysis: string;
  emotionalJourney: EmotionalJourneyPoint[];
  timeline: NarrativeTimelineEntry[];
}

export interface CombatExportData {
  combatContext: CombatContext;
  eventHistory: CombatEvent[];
  conversationHistory: Array<[string, any]>;
  systemMetrics: SystemMetrics;
  narrativeHistory: NarrativeElement[];
  enhancements: any[];
  exportTimestamp: Date;
  version: string;
}

interface SystemMetrics {
  dialoguesProcessed: number;
  enhancementsProcessed: number;
  averageProcessingTime: number;
  totalProcessingTime: number;
  highValueDialogues: number;
  complexMechanics: number;
  contextUpdates: number;
}

type NarrativeTimeframe = 'last_minute' | 'last_5_minutes' | 'last_round' | 'entire_combat';

interface EmotionalJourneyPoint {
  timestamp: Date;
  emotion: string;
  intensity: number;
  source: string;
}

interface NarrativeTimelineEntry {
  timestamp: Date;
  type: string;
  description: string;
  speaker?: string;
  cinematic: boolean;
}