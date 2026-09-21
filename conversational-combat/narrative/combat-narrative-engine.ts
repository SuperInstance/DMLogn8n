/**
 * Combat Narrative Engine
 * Generates dynamic, cinematic combat descriptions and integrates dialogue with action
 */

import {
  CombatDialogue,
  NarrativeElement,
  CombatAction,
  Character,
  CombatContext,
  CombatEvent,
  DialogueMechanics
} from '../types';
import { NARRATIVE_TEMPLATES, COMBAT_INTENSITIES } from '../utils/constants';

export class CombatNarrativeEngine {
  private narrativeHistory: NarrativeElement[] = [];
  private characterVoiceProfiles: Map<string, VoiceProfile> = new Map();
  private combatIntensity: number = 0.5;
  private environmentalDescriptions: Map<string, string[]> = new Map();
  private cinematicTriggers: CinematicTrigger[] = [];

  constructor() {
    this.initializeVoiceProfiles();
    this.initializeEnvironmentalDescriptions();
    this.initializeCinematicTriggers();
  }

  /**
   * Generate narrative for dialogue and combat action
   */
  public generateCombatNarrative(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): NarrativeElement[] {
    const narrativeElements: NarrativeElement[] = [];

    // Update combat intensity
    this.updateCombatIntensity(dialogue, mechanics, context);

    // Generate action description
    const actionNarrative = this.generateActionNarrative(dialogue, mechanics, context);
    narrativeElements.push(actionNarrative);

    // Generate character dialogue with voice
    const dialogueNarrative = this.generateDialogueNarrative(dialogue, context);
    narrativeElements.push(dialogueNarrative);

    // Generate environmental interaction
    const environmentalNarrative = this.generateEnvironmentalNarrative(dialogue, mechanics, context);
    if (environmentalNarrative) {
      narrativeElements.push(environmentalNarrative);
    }

    // Generate cinematic moments
    const cinematicNarrative = this.generateCinematicNarrative(dialogue, mechanics, context);
    if (cinematicNarrative) {
      narrativeElements.push(cinematicNarrative);
    }

    // Generate team coordination narrative
    const coordinationNarrative = this.generateCoordinationNarrative(dialogue, context);
    if (coordinationNarrative) {
      narrativeElements.push(coordinationNarrative);
    }

    // Store in history
    this.narrativeHistory.push(...narrativeElements);

    return narrativeElements;
  }

  /**
   * Generate action-focused narrative
   */
  private generateActionNarrative(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): NarrativeElement {
    const character = this.getCharacter(dialogue.characterId, context);
    const action = mechanics.combatAction;
    const intensity = this.getCombatIntensityDescription();

    let template = '';
    let content = '';

    // Select appropriate template based on action type
    if (action.type === 'weapon_attack') {
      template = this.selectAttackTemplate(dialogue, mechanics);
    } else if (action.type === 'spell_cast') {
      template = this.selectSpellTemplate(dialogue, mechanics);
    } else if (action.type === 'skill_check') {
      template = this.selectSkillTemplate(dialogue, mechanics);
    } else {
      template = NARRATIVE_TEMPLATES.dramatic_moment[0];
    }

    // Fill template with appropriate content
    content = this.fillNarrativeTemplate(template, dialogue, mechanics, context);

    return {
      id: this.generateNarrativeId(),
      type: 'action',
      content,
      speaker: character.name,
      tone: this.getNarrativeTone(dialogue, context),
      cinematic: this.shouldBeCinematic(dialogue, mechanics, context)
    };
  }

  /**
   * Generate dialogue narrative with character voice
   */
  private generateDialogueNarrative(
    dialogue: CombatDialogue,
    context: CombatContext
  ): NarrativeElement {
    const character = this.getCharacter(dialogue.characterId, context);
    const voiceProfile = this.characterVoiceProfiles.get(character.id);
    const enhancedText = voiceProfile ?
      this.applyCharacterVoice(dialogue.text, voiceProfile) :
      dialogue.text;

    return {
      id: this.generateNarrativeId(),
      type: 'dialogue',
      content: enhancedText,
      speaker: character.name,
      tone: this.getEmotionalTone(dialogue.intent?.emotionalTone),
      cinematic: dialogue.intent?.strategicValue > 0.8 || false
    };
  }

  /**
   * Generate environmental interaction narrative
   */
  private generateEnvironmentalNarrative(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): NarrativeElement | null {
    const character = this.getCharacter(dialogue.characterId, context);
    const environment = context.environment;

    // Check for environmental interactions
    const interaction = this.findEnvironmentalInteraction(dialogue, mechanics, environment);
    if (!interaction) return null;

    return {
      id: this.generateNarrativeId(),
      type: 'description',
      content: interaction,
      speaker: undefined,
      tone: 'descriptive',
      cinematic: interaction.includes('dramatic') || interaction.includes('spectacular')
    };
  }

  /**
   * Generate cinematic moments
   */
  private generateCinematicNarrative(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): NarrativeElement | null {
    if (!this.shouldBeCinematic(dialogue, mechanics, context)) {
      return null;
    }

    const cinematicMoment = this.createCinematicMoment(dialogue, mechanics, context);

    return {
      id: this.generateNarrativeId(),
      type: 'effect',
      content: cinematicMoment,
      speaker: undefined,
      tone: 'epic',
      cinematic: true
    };
  }

  /**
   * Generate team coordination narrative
   */
  private generateCoordinationNarrative(
    dialogue: CombatDialogue,
    context: CombatContext
  ): NarrativeElement | null {
    if (dialogue.intent?.type !== 'coordinate') return null;

    const character = this.getCharacter(dialogue.characterId, context);
    const allies = this.getAllies(character, context);

    const coordinationText = this.generateCoordinationText(character, allies, dialogue);

    return {
      id: this.generateNarrativeId(),
      type: 'description',
      content: coordinationText,
      speaker: character.name,
      tone: 'tactical',
      cinematic: allies.length >= 3
    };
  }

  /**
   * Select appropriate attack template
   */
  private selectAttackTemplate(dialogue: CombatDialogue, mechanics: DialogueMechanics): string {
    const templates = NARRATIVE_TEMPLATES.attack_start;

    // Select template based on emotional tone and strategy
    if (dialogue.intent?.emotionalTone.anger > 0.7) {
      return templates[0]; // Aggressive template
    } else if (dialogue.intent?.strategicValue > 0.7) {
      return templates[1]; // Tactical template
    } else {
      return templates[2]; // Standard template
    }
  }

  /**
   * Select appropriate spell template
   */
  private selectSpellTemplate(dialogue: CombatDialogue, mechanics: DialogueMechanics): string {
    return NARRATIVE_TEMPLATES.spell_cast[0];
  }

  /**
   * Select appropriate skill template
   */
  private selectSkillTemplate(dialogue: CombatDialogue, mechanics: DialogueMechanics): string {
    if (mechanics.combatAction.actionName?.includes('defend')) {
      return NARRATIVE_TEMPLATES.defense[0];
    }
    return NARRATIVE_TEMPLATES.dramatic_moment[0];
  }

  /**
   * Fill narrative template with dynamic content
   */
  private fillNarrativeTemplate(
    template: string,
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): string {
    const character = this.getCharacter(dialogue.characterId, context);
    const replacements: { [key: string]: string } = {
      '{character}': character.name,
      '{dialogue}': dialogue.text,
      '{intensity}': this.getCombatIntensityDescription(),
      '{adjective}': this.getActionAdjective(dialogue, mechanics),
      '{noun}': this.getActionNoun(mechanics),
      '{verb}': this.getActionVerb(mechanics),
      '{target}': this.getTargetName(dialogue.target, context),
      '{weapon}': this.getWeaponName(character),
      '{spell_energy}': this.getSpellEnergyDescription(mechanics),
      '{form_around_character}': 'begins to form around them',
      '{spell_effect}': 'magical energy',
      '{result}': this.getActionResult(mechanics),
      '{moment_type}': 'critical moment',
      '{dramatic_event}': 'the tide of battle shifts',
      '{dramatic_description}': 'in a display of incredible skill',
      '{defense_action}': this.getDefenseAction(mechanics)
    };

    let filledTemplate = template;
    for (const [placeholder, replacement] of Object.entries(replacements)) {
      filledTemplate = filledTemplate.replace(new RegExp(placeholder, 'g'), replacement);
    }

    return filledTemplate;
  }

  /**
   * Apply character voice to dialogue
   */
  private applyCharacterVoice(text: string, voiceProfile: VoiceProfile): string {
    let modifiedText = text;

    // Apply vocabulary adjustments
    if (voiceProfile.vocabulary === 'formal') {
      modifiedText = this.formalizeText(modifiedText);
    } else if (voiceProfile.vocabulary === 'aggressive') {
      modifiedText = this.aggressivizeText(modifiedText);
    } else if (voiceProfile.vocabulary === 'poetic') {
      modifiedText = this.poeticizeText(modifiedText);
    }

    // Apply sentence structure adjustments
    modifiedText = this.adjustSentenceStructure(modifiedText, voiceProfile.sentenceStructure);

    // Add character-specific phrases
    modifiedText = this.addCharacterPhrases(modifiedText, voiceProfile.commonPhrases);

    return modifiedText;
  }

  /**
   * Update combat intensity based on recent events
   */
  private updateCombatIntensity(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): void {
    let intensityChange = 0;

    // Base intensity from action type
    if (mechanics.combatAction.type === 'weapon_attack') {
      intensityChange = 0.1;
    } else if (mechanics.combatAction.type === 'spell_cast') {
      intensityChange = 0.15;
    }

    // Emotional intensity
    if (dialogue.intent) {
      intensityChange += (dialogue.intent.emotionalTone.anger +
                        dialogue.intent.emotionalTone.desperation) * 0.2;
      intensityChange += dialogue.intent.strategicValue * 0.1;
    }

    // Damage/healing magnitude
    if (mechanics.combatAction.damage) {
      intensityChange += mechanics.combatAction.damage.amount * 0.01;
    }

    this.combatIntensity = Math.min(1, Math.max(0, this.combatIntensity + intensityChange));
  }

  /**
   * Get combat intensity description
   */
  private getCombatIntensityDescription(): string {
    for (const [name, config] of Object.entries(COMBAT_INTENSITIES)) {
      if (this.combatIntensity <= config.threshold) {
        return config.description;
      }
    }
    return COMBAT_INTENSITIES.desperate.description;
  }

  /**
   * Determine if narrative should be cinematic
   */
  private shouldBeCinematic(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): boolean {
    // Critical hits
    if (mechanics.combatAction.damage?.critical) return true;

    // High strategic value
    if (dialogue.intent?.strategicValue > 0.8) return true;

    // High emotional intensity
    if (dialogue.intent && this.getMaxEmotion(dialogue.intent.emotionalTone) > 0.8) return true;

    // Environmental interactions
    if (this.hasEnvironmentalInteraction(dialogue, mechanics, context)) return true;

    // Multi-character coordination
    if (dialogue.intent?.type === 'coordinate' && this.getAlliesCount(dialogue.characterId, context) >= 3) {
      return true;
    }

    return false;
  }

  /**
   * Create cinematic moment description
   */
  private createCinematicMoment(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): string {
    const cinematicTemplates = [
      "Time seems to slow as {character} {action} with {intensity} determination.",
      "The battlefield falls silent for a moment as {character}'s {action} unfolds.",
      "In a display of incredible skill, {character} {action} while {dialogue}.",
      "The air crackles with energy as {character} {action} with devastating effect.",
      "{dialogue} echoes across the battlefield as {character} {action}."
    ];

    const template = cinematicTemplates[Math.floor(Math.random() * cinematicTemplates.length)];
    return this.fillCinematicTemplate(template, dialogue, mechanics, context);
  }

  /**
   * Fill cinematic template
   */
  private fillCinematicTemplate(
    template: string,
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): string {
    const character = this.getCharacter(dialogue.characterId, context);
    const action = this.getActionDescription(mechanics);

    return template
      .replace('{character}', character.name)
      .replace('{action}', action)
      .replace('{intensity}', this.getCombatIntensityDescription())
      .replace('{dialogue}', dialogue.text);
  }

  /**
   * Get character from context
   */
  private getCharacter(characterId: string, context: CombatContext): Character {
    return context.characters.find(c => c.id === characterId) || context.characters[0];
  }

  /**
   * Get action description
   */
  private getActionDescription(mechanics: DialogueMechanics): string {
    const action = mechanics.combatAction;
    if (action.actionName) return action.actionName;
    if (action.type === 'weapon_attack') return 'strikes with their weapon';
    if (action.type === 'spell_cast') return 'casts a spell';
    return 'acts';
  }

  /**
   * Get target name
   */
  private getTargetName(targetId: string | undefined, context: CombatContext): string {
    if (!targetId) return 'their target';
    const target = context.characters.find(c => c.id === targetId);
    return target ? target.name : 'their foe';
  }

  /**
   * Get weapon name
   */
  private getWeaponName(character: Character): string {
    const weapon = character.equipment.find(e => e.type === 'weapon');
    return weapon ? weapon.name : 'weapon';
  }

  // Text transformation methods

  private formalizeText(text: string): string {
    return text
      .replace(/\bgonna\b/gi, 'going to')
      .replace(/\bwanna\b/gi, 'want to')
      .replace(/\bgotta\b/gi, 'must')
      .replace(/\byeah\b/gi, 'indeed')
      .replace(/\bcool\b/gi, 'excellent');
  }

  private aggressivizeText(text: string): string {
    return text
      .replace(/\bhit\b/gi, 'CRUSH')
      .replace(/\bgo\b/gi, 'CHARGE')
      .replace(/\bstop\b/gi, 'HALT')
      .replace(/\bkill\b/gi, 'DESTROY');
  }

  private poeticizeText(text: string): string {
    return text
      .replace(/\brun\b/gi, 'dance')
      .replace(/\bfight\b/gi, 'engage in the deadly ballet')
      .replace(/\blood\b/gi, 'crimson rivers')
      .replace(/\bdeath\b/gi, 'the final silence');
  }

  private adjustSentenceStructure(text: string, structure: string): string {
    // Implementation would adjust sentence complexity
    return text;
  }

  private addCharacterPhrases(text: string, phrases: string[]): string {
    if (phrases.length === 0) return text;
    const phrase = phrases[Math.floor(Math.random() * phrases.length)];
    return `${text} ${phrase}`;
  }

  // Helper methods

  private getActionAdjective(dialogue: CombatDialogue, mechanics: DialogueMechanics): string {
    if (dialogue.intent?.emotionalTone.anger > 0.7) return 'furious';
    if (dialogue.intent?.strategicValue > 0.7) return 'calculated';
    return 'swift';
  }

  private getActionNoun(mechanics: DialogueMechanics): string {
    if (mechanics.combatAction.type === 'weapon_attack') return 'assault';
    if (mechanics.combatAction.type === 'spell_cast') return 'incantation';
    return 'maneuver';
  }

  private getActionVerb(mechanics: DialogueMechanics): string {
    if (mechanics.combatAction.type === 'weapon_attack') return 'strikes';
    if (mechanics.combatAction.type === 'spell_cast') return 'chants';
    return 'acts';
  }

  private getSpellEnergyDescription(mechanics: DialogueMechanics): string {
    return 'mystical energy';
  }

  private getActionResult(mechanics: DialogueMechanics): string {
    return 'impacts with force';
  }

  private getDefenseAction(mechanics: DialogueMechanics): string {
    return 'defends against the assault';
  }

  private getEmotionalTone(emotionalTone?: any): string {
    if (!emotionalTone) return 'neutral';

    const maxEmotion = Object.entries(emotionalTone).reduce((a, b) =>
      emotionalTone[a[0] as keyof typeof emotionalTone] > emotionalTone[b[0] as keyof typeof emotionalTone] ? a : b
    );

    return maxEmotion[0];
  }

  private getMaxEmotion(emotionalTone: any): number {
    return Math.max(...Object.values(emotionalTone));
  }

  private findEnvironmentalInteraction(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    environment: any
  ): string | null {
    // Implementation would check for specific environmental interactions
    return null;
  }

  private hasEnvironmentalInteraction(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    context: CombatContext
  ): boolean {
    return false; // Placeholder
  }

  private getAllies(character: Character, context: CombatContext): Character[] {
    return context.characters.filter(c => c.id !== character.id);
  }

  private getAlliesCount(characterId: string, context: CombatContext): number {
    return context.characters.filter(c => c.id !== characterId).length;
  }

  private generateCoordinationText(character: Character, allies: Character[], dialogue: CombatDialogue): string {
    const allyNames = allies.map(a => a.name).join(', ');
    return `${character.name} coordinates with ${allyNames}: "${dialogue.text}"`;
  }

  private generateNarrativeId(): string {
    return `narrative_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getNarrativeTone(dialogue: CombatDialogue, context: CombatContext): string {
    if (!dialogue.intent) return 'neutral';

    if (dialogue.intent.emotionalTone.anger > 0.6) return 'aggressive';
    if (dialogue.intent.emotionalTone.confidence > 0.6) return 'confident';
    if (dialogue.intent.emotionalTone.humor > 0.6) return 'humorous';
    if (dialogue.intent.emotionalTone.seriousness > 0.6) return 'serious';

    return 'neutral';
  }

  // Initialization methods

  private initializeVoiceProfiles(): void {
    // Default voice profiles would be initialized here
  }

  private initializeEnvironmentalDescriptions(): void {
    // Environmental descriptions would be initialized here
  }

  private initializeCinematicTriggers(): void {
    this.cinematicTriggers = [
      { type: 'critical_hit', threshold: 0.95 },
      { type: 'coordinated_attack', threshold: 0.8 },
      { type: 'environmental_interaction', threshold: 0.7 },
      { type: 'emotional_peak', threshold: 0.9 }
    ];
  }

  // Public methods

  public getNarrativeHistory(): NarrativeElement[] {
    return this.narrativeHistory;
  }

  public getCombatIntensity(): number {
    return this.combatIntensity;
  }

  public resetIntensity(): void {
    this.combatIntensity = 0.5;
  }

  public clearHistory(): void {
    this.narrativeHistory = [];
  }
}

interface VoiceProfile {
  vocabulary: 'formal' | 'casual' | 'aggressive' | 'poetic' | 'technical' | 'simple';
  sentenceStructure: 'complex' | 'simple' | 'fragmented' | 'flowery';
  commonPhrases: string[];
  accents: string[];
  tics: string[];
}

interface CinematicTrigger {
  type: string;
  threshold: number;
}