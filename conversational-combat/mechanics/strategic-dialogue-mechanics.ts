/**
 * Strategic Dialogue Mechanics System
 * Implements dialogue-based combat mechanics and tactical advantages
 */

import {
  DialogueIntent,
  DialogueMechanics,
  MechanicalBonus,
  Character,
  CombatContext,
  BattleCry,
  TacticalCommunication,
  MoraleState,
  DialogueEffect
} from '../types';
import { DIALOGUE_BONUSES, BATTLE_CRY_TEMPLATES, TACTICAL_PATTERNS } from '../utils/constants';

export class StrategicDialogueMechanics {
  private activeBattleCries: Map<string, BattleCry[]> = new Map();
  private tacticalCommunications: TacticalCommunication[] = [];
  private moraleStates: Map<string, number> = new Map();
  private dialogueHistory: Map<string, DialogueIntent[]> = new Map();

  constructor() {
    this.initializeMoraleTracking();
  }

  /**
   * Process dialogue and generate strategic effects
   */
  public processStrategicDialogue(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): DialogueMechanics {
    const mechanics = this.generateBaseMechanics(intent, character, context);

    // Apply strategic enhancements
    this.applyStrategicEnhancements(mechanics, intent, character, context);
    this.updateMorale(intent, character, context);
    this.checkBattleCryTriggers(intent, character, context);
    this.processTacticalCommunication(intent, character, context);

    return mechanics;
  }

  /**
   * Generate base mechanics from dialogue intent
   */
  private generateBaseMechanics(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): DialogueMechanics {
    const bonuses = this.generateStrategicBonuses(intent, character, context);
    const resourceCosts = this.calculateResourceCosts(intent, character);
    const duration = this.calculateEffectDuration(intent, context);
    const conditions = this.determineConditions(intent, character, context);
    const synergies = this.identifySynergies(intent, character, context);

    return {
      combatAction: this.createCombatAction(intent, character),
      bonuses,
      resourceCosts,
      duration,
      conditions,
      synergies
    };
  }

  /**
   * Generate strategic bonuses based on dialogue type and context
   */
  private generateStrategicBonuses(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): MechanicalBonus[] {
    const bonuses: MechanicalBonus[] = [];

    // Base bonuses from dialogue type
    const baseBonuses = this.getBaseDialogueBonuses(intent);
    bonuses.push(...baseBonuses);

    // Strategic positioning bonuses
    const positionBonuses = this.getPositioningBonuses(intent, character, context);
    bonuses.push(...positionBonuses);

    // Team coordination bonuses
    const teamBonuses = this.getTeamCoordinationBonuses(intent, character, context);
    bonuses.push(...teamBonuses);

    // Emotional state bonuses
    const emotionalBonuses = this.getEmotionalStateBonuses(intent, character);
    bonuses.push(...emotionalBonuses);

    // Contextual bonuses
    const contextualBonuses = this.getContextualBonuses(intent, character, context);
    bonuses.push(...contextualBonuses);

    return bonuses;
  }

  /**
   * Get base bonuses from dialogue type
   */
  private getBaseDialogueBonuses(intent: DialogueIntent): MechanicalBonus[] {
    const bonuses: MechanicalBonus[] = [];
    const dialogueBonuses = DIALOGUE_BONUSES[intent.type];

    if (!dialogueBonuses) return bonuses;

    // Advantage bonuses
    if (dialogueBonuses.advantage) {
      bonuses.push({
        type: 'advantage',
        value: 1,
        source: `${intent.type}_dialogue`,
        appliesTo: dialogueBonuses.advantage,
        duration: dialogueBonuses.duration
      });
    }

    // Disadvantage bonuses for enemies
    if (dialogueBonuses.disadvantage) {
      bonuses.push({
        type: 'disadvantage',
        value: 1,
        source: `${intent.type}_dialogue`,
        appliesTo: dialogueBonuses.disadvantage,
        duration: dialogueBonuses.duration
      });
    }

    // Numerical bonuses
    if (dialogueBonuses.bonus) {
      bonuses.push({
        ...dialogueBonuses.bonus,
        source: `${intent.type}_dialogue`,
        duration: dialogueBonuses.duration
      });
    }

    // Inspiration bonuses
    if (dialogueBonuses.inspiration) {
      bonuses.push({
        type: 'inspiration',
        value: 1,
        source: 'inspiring_dialogue',
        appliesTo: ['all'],
        duration: 0
      });
    }

    return bonuses;
  }

  /**
   * Get positioning-based bonuses
   */
  private getPositioningBonuses(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): MechanicalBonus[] {
    const bonuses: MechanicalBonus[] = [];

    // Flanking bonuses with dialogue coordination
    if (this.isFlanking(character, context) && intent.type === 'coordinate') {
      bonuses.push({
        type: 'bonus',
        value: 2,
        source: 'flanking_coordination',
        appliesTo: ['attack', 'damage'],
        duration: 1
      });
    }

    // High ground intimidation
    if (this.hasHighGround(character, context) && intent.type === 'intimidate') {
      bonuses.push({
        type: 'bonus',
        value: 2,
        source: 'high_ground_intimidation',
        appliesTo: ['intimidation'],
        duration: 1
      });
    }

    // Cover-based deception
    if (this.hasCover(character, context) && intent.type === 'deceive') {
      bonuses.push({
        type: 'bonus',
        value: 3,
        source: 'cover_deception',
        appliesTo: ['stealth', 'deception'],
        duration: 2
      });
    }

    return bonuses;
  }

  /**
   * Get team coordination bonuses
   */
  private getTeamCoordinationBonuses(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): MechanicalBonus[] {
    const bonuses: MechanicalBonus[] = [];

    if (intent.type !== 'coordinate') return bonuses;

    // Count nearby allies
    const nearbyAllies = this.getNearbyAllies(character, context);

    // Teamwork scaling bonus
    if (nearbyAllies.length >= 2) {
      bonuses.push({
        type: 'bonus',
        value: nearbyAllies.length,
        source: 'teamwork_scaling',
        appliesTo: ['all_ally_checks'],
        duration: 1
      });
    }

    // Class synergy bonuses
    const classSynergy = this.getClassSynergyBonus(character, nearbyAllies);
    if (classSynergy) {
      bonuses.push(classSynergy);
    }

    return bonuses;
  }

  /**
   * Get emotional state bonuses
   */
  private getEmotionalStateBonuses(intent: DialogueIntent, character: Character): MechanicalBonus[] {
    const bonuses: MechanicalBonus[] = [];

    // Confidence-based damage bonus
    if (intent.emotionalTone.confidence > 0.7) {
      bonuses.push({
        type: 'bonus',
        value: Math.floor(intent.emotionalTone.confidence * 3),
        source: 'confidence_damage',
        appliesTo: ['damage'],
        duration: 1
      });
    }

    // Anger-based attack bonus
    if (intent.emotionalTone.anger > 0.6) {
      bonuses.push({
        type: 'bonus',
        value: Math.floor(intent.emotionalTone.anger * 2),
        source: 'rage_bonus',
        appliesTo: ['attack'],
        duration: 1
      });
    }

    // Fear-based defense bonus
    if (intent.emotionalTone.fear > 0.5) {
      bonuses.push({
        type: 'bonus',
        value: Math.floor(intent.emotionalTone.fear * 2),
        source: 'desperate_defense',
        appliesTo: ['defense'],
        duration: 1
      });
    }

    // Humor-based morale bonus
    if (intent.emotionalTone.humor > 0.6) {
      bonuses.push({
        type: 'bonus',
        value: 1,
        source: 'morale_boost',
        appliesTo: ['morale_saves'],
        duration: 3
      });
    }

    return bonuses;
  }

  /**
   * Get contextual bonuses based on combat state
   */
  private getContextualBonuses(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): MechanicalBonus[] {
    const bonuses: MechanicalBonus[] = [];

    // Desperation bonuses
    const characterMorale = this.moraleStates.get(character.id) || 0.5;
    if (characterMorale < 0.3) {
      bonuses.push({
        type: 'bonus',
        value: 3,
        source: 'desperation_bonus',
        appliesTo: ['all_checks'],
        duration: 1
      });
    }

    // Leadership bonuses
    if (this.isLeader(character, context) && intent.type === 'coordinate') {
      bonuses.push({
        type: 'bonus',
        value: 2,
        source: 'leadership_coordination',
        appliesTo: ['all_ally_checks'],
        duration: 2
      });
    }

    // Surprise round bonuses
    if (context.state.phase === 'surprise' && intent.type === 'deceive') {
      bonuses.push({
        type: 'advantage',
        value: 1,
        source: 'surprise_deception',
        appliesTo: ['initiative', 'attack'],
        duration: 1
      });
    }

    return bonuses;
  }

  /**
   * Apply strategic enhancements to mechanics
   */
  private applyStrategicEnhancements(
    mechanics: DialogueMechanics,
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): void {
    // Apply scaling based on strategic value
    if (intent.strategicValue > 0.8) {
      mechanics.bonuses.push({
        type: 'bonus',
        value: 2,
        source: 'strategic_genius',
        appliesTo: ['primary_action'],
        duration: mechanics.duration
      });
    }

    // Apply combo bonuses
    const comboBonus = this.checkComboPotential(intent, character, context);
    if (comboBonus) {
      mechanics.bonuses.push(comboBonus);
    }

    // Apply situational modifiers
    this.applySituationalModifiers(mechanics, intent, character, context);
  }

  /**
   * Calculate resource costs for dialogue actions
   */
  private calculateResourceCosts(intent: DialogueIntent, character: Character): any[] {
    const costs = [];

    // Base action cost
    costs.push({
      type: 'action',
      amount: 1
    });

    // Reduced cost for high charisma characters
    const charismaMod = Math.floor((character.abilities.charisma - 10) / 2);
    if (charismaMod >= 3 && ['intimidate', 'persuade', 'deceive'].includes(intent.type)) {
      costs[0].type = 'bonus_action';
    }

    // Superiority dice for battle master maneuvers
    if (character.class.toLowerCase().includes('fighter') &&
        character.class.toLowerCase().includes('battle master')) {
      costs.push({
        type: 'superiority_dice',
        amount: 1,
        source: 'dialogue_maneuver'
      });
    }

    return costs;
  }

  /**
   * Calculate effect duration
   */
  private calculateEffectDuration(intent: DialogueIntent, context: CombatContext): number {
    let duration = 1;

    // Base duration by intent type
    const durationMap = {
      intimidate: 1,
      taunt: 1,
      persuade: 3,
      deceive: 2,
      coordinate: 1,
      buff: 3,
      debuff: 2,
      attack: 0,
      defend: 1,
      spell: 2
    };

    duration = durationMap[intent.type] || 1;

    // Strategic value extends duration
    duration += Math.floor(intent.strategicValue * 2);

    // High confidence extends duration
    if (intent.emotionalTone.confidence > 0.7) {
      duration += 1;
    }

    return Math.min(10, duration);
  }

  /**
   * Determine conditions applied by dialogue
   */
  private determineConditions(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): string[] {
    const conditions = [];

    // Intent-based conditions
    switch (intent.type) {
      case 'intimidate':
        if (intent.emotionalTone.confidence > 0.6) {
          conditions.push('Frightened');
        }
        break;
      case 'taunt':
        if (intent.emotionalTone.humor > 0.5 || intent.emotionalTone.anger > 0.5) {
          conditions.push('Rattled');
        }
        break;
      case 'deceive':
        if (intent.confidence > 0.7) {
          conditions.push('Deceived');
        }
        break;
      case 'persuade':
        if (intent.emotionalTone.confidence > 0.7) {
          conditions.push('Charmed');
        }
        break;
    }

    // Character-specific conditions
    if (character.class.toLowerCase().includes('paladin') && intent.type === 'intimidate') {
      conditions.push('Smite-Struck');
    }

    if (character.class.toLowerCase().includes('rogue') && intent.type === 'taunt') {
      conditions.push('Off-Balance');
    }

    return conditions;
  }

  /**
   * Identify synergies with other characters and actions
   */
  private identifySynergies(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): string[] {
    const synergies = [];

    // Character class synergies
    const classSynergies = this.getClassSynergies(character, context);
    synergies.push(...classSynergies);

    // Positional synergies
    const positionalSynergies = this.getPositionalSynergies(character, context);
    synergies.push(...positionalSynergies);

    // Intent-based synergies
    const intentSynergies = this.getIntentSynergies(intent, context);
    synergies.push(...intentSynergies);

    return synergies;
  }

  /**
   * Check for battle cry triggers
   */
  private checkBattleCryTriggers(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): void {
    const battleCryTriggers = [
      { type: 'attack', threshold: 0.8, emotion: 'confidence' },
      { type: 'intimidate', threshold: 0.7, emotion: 'anger' },
      { type: 'coordinate', threshold: 0.6, emotion: 'confidence' }
    ];

    for (const trigger of battleCryTriggers) {
      if (intent.type === trigger.type &&
          intent.strategicValue > trigger.threshold &&
          intent.emotionalTone[trigger.emotion as keyof typeof intent.emotionalTone] > 0.7) {
        this.triggerBattleCry(character, context);
        break;
      }
    }
  }

  /**
   * Trigger a battle cry effect
   */
  private triggerBattleCry(character: Character, context: CombatContext): void {
    const characterClass = character.class.toLowerCase();
    let template = BATTLE_CRY_TEMPLATES.warrior;

    // Select appropriate template based on class
    if (characterClass.includes('mage') || characterClass.includes('wizard')) {
      template = BATTLE_CRY_TEMPLATES.mage;
    } else if (characterClass.includes('rogue')) {
      template = BATTLE_CRY_TEMPLATES.rogue;
    } else if (characterClass.includes('cleric')) {
      template = BATTLE_CRY_TEMPLATES.cleric;
    } else if (characterClass.includes('ranger')) {
      template = BATTLE_CRY_TEMPLATES.ranger;
    }

    const battleCry: BattleCry = {
      phrase: template[Math.floor(Math.random() * template.length)],
      effect: {
        type: 'buff',
        targets: 'allies',
        range: 30,
        duration: 3,
        mechanicalBonus: [{
          type: 'bonus',
          value: 2,
          source: 'battle_cry',
          appliesTo: ['attack', 'damage'],
          duration: 3
        }]
      },
      cooldown: 3,
      uses: 1,
      characterTrait: 'leader'
    };

    // Store active battle cry
    if (!this.activeBattleCries.has(character.id)) {
      this.activeBattleCries.set(character.id, []);
    }
    this.activeBattleCries.get(character.id)!.push(battleCry);
  }

  /**
   * Process tactical communication
   */
  private processTacticalCommunication(
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): void {
    if (intent.type !== 'coordinate') return;

    const text = intent.flavor || '';
    let communicationType: TacticalCommunication['type'] = 'suggest';
    let priority = 1;
    let urgency = 0.5;

    // Determine communication type
    for (const [type, patterns] of Object.entries(TACTICAL_PATTERNS)) {
      for (const pattern of patterns) {
        if (text.toLowerCase().includes(pattern)) {
          communicationType = type as TacticalCommunication['type'];
          break;
        }
      }
    }

    // Calculate priority and urgency
    priority = Math.floor(intent.strategicValue * 3);
    urgency = Math.max(intent.emotionalTone.desperation, intent.emotionalTone.anger);

    const tacticalComm: TacticalCommunication = {
      type: communicationType,
      priority,
      urgency,
      targets: this.getTacticalTargets(intent, context),
      content: text,
      expectedOutcome: this.calculateExpectedOutcome(intent, character, context)
    };

    this.tacticalCommunications.push(tacticalComm);
  }

  // Helper methods

  private isFlanking(character: Character, context: CombatContext): boolean {
    // Implementation would check positioning relative to enemies
    return false; // Placeholder
  }

  private hasHighGround(character: Character, context: CombatContext): boolean {
    return character.position.z > 5; // Placeholder
  }

  private hasCover(character: Character, context: CombatContext): boolean {
    return character.position.cover !== 'none';
  }

  private getNearbyAllies(character: Character, context: CombatContext): Character[] {
    return context.characters.filter(other =>
      other.id !== character.id &&
      this.getDistance(character.position, other.position) <= 30
    );
  }

  private getDistance(pos1: any, pos2: any): number {
    return Math.sqrt(Math.pow(pos1.x - pos2.x, 2) + Math.pow(pos1.y - pos2.y, 2));
  }

  private getClassSynergyBonus(character: Character, allies: Character[]): MechanicalBonus | null {
    // Check for class synergies
    for (const ally of allies) {
      if (this.hasClassSynergy(character, ally)) {
        return {
          type: 'bonus',
          value: 2,
          source: 'class_synergy',
          appliesTo: ['damage', 'attack'],
          duration: 1
        };
      }
    }
    return null;
  }

  private hasClassSynergy(char1: Character, char2: Character): boolean {
    const synergies = [
      ['Paladin', 'Cleric'],
      ['Rogue', 'Ranger'],
      ['Wizard', 'Sorcerer'],
      ['Fighter', 'Barbarian']
    ];

    return synergies.some(([class1, class2]) =>
      (char1.class.includes(class1) && char2.class.includes(class2)) ||
      (char1.class.includes(class2) && char2.class.includes(class1))
    );
  }

  private isLeader(character: Character, context: CombatContext): boolean {
    // Check if character is party leader based on class, level, or explicit designation
    return character.level >= 10 ||
           character.class.includes('Paladin') ||
           character.class.includes('Cleric');
  }

  private checkComboPotential(intent: DialogueIntent, character: Character, context: CombatContext): MechanicalBonus | null {
    // Check for potential combos with previous actions
    const recentIntent = this.dialogueHistory.get(character.id)?.slice(-1)[0];

    if (recentIntent && this.isCombo(recentIntent, intent)) {
      return {
        type: 'bonus',
        value: 3,
        source: 'combo_bonus',
        appliesTo: ['primary_action'],
        duration: 1
      };
    }

    return null;
  }

  private isCombo(intent1: DialogueIntent, intent2: DialogueIntent): boolean {
    // Define combo patterns
    const comboPatterns = [
      ['intimidate', 'attack'],
      ['deceive', 'attack'],
      ['coordinate', 'buff'],
      ['taunt', 'debuff']
    ];

    return comboPatterns.some(([first, second]) =>
      intent1.type === first && intent2.type === second
    );
  }

  private applySituationalModifiers(
    mechanics: DialogueMechanics,
    intent: DialogueIntent,
    character: Character,
    context: CombatContext
  ): void {
    // Apply environmental modifiers
    // Apply time-of-day modifiers
    // Apply weather modifiers
    // Apply lighting modifiers
  }

  private getClassSynergies(character: Character, context: CombatContext): string[] {
    const synergies = [];

    for (const other of context.characters) {
      if (other.id === character.id) continue;

      if (this.hasClassSynergy(character, other)) {
        synergies.push(`${character.class}_${other.class}_synergy`);
      }
    }

    return synergies;
  }

  private getPositionalSynergies(character: Character, context: CombatContext): string[] {
    const synergies = [];

    if (this.isFlanking(character, context)) {
      synergies.push('flanking_position');
    }

    if (this.hasHighGround(character, context)) {
      synergies.push('high_ground_advantage');
    }

    return synergies;
  }

  private getIntentSynergies(intent: DialogueIntent, context: CombatContext): string[] {
    const synergies = [];

    // Check for multi-character intent coordination
    const coordinatedIntents = context.characters.filter(char =>
      this.dialogueHistory.get(char.id)?.slice(-1)[0]?.type === intent.type
    );

    if (coordinatedIntents.length >= 2) {
      synergies.push('multi_character_coordination');
    }

    return synergies;
  }

  private createCombatAction(intent: DialogueIntent, character: Character): any {
    return {
      type: intent.type === 'attack' ? 'weapon_attack' : 'skill_check',
      actionName: intent.action || `${intent.type}_action`,
      damage: intent.type === 'attack' ? {
        amount: this.calculateDamage(character, intent),
        type: 'bludgeoning',
        bonus: this.calculateDamageBonus(character, intent),
        critical: false
      } : undefined
    };
  }

  private calculateDamage(character: Character, intent: DialogueIntent): number {
    return 4 + Math.floor((character.abilities.strength - 10) / 2);
  }

  private calculateDamageBonus(character: Character, intent: DialogueIntent): number {
    return Math.floor(intent.strategicValue * 3);
  }

  private updateMorale(intent: DialogueIntent, character: Character, context: CombatContext): void {
    const currentMorale = this.moraleStates.get(character.id) || 0.5;

    let moraleChange = 0;

    if (intent.type === 'intimidate' && intent.emotionalTone.confidence > 0.7) {
      moraleChange = 0.1;
    }

    if (intent.type === 'coordinate') {
      moraleChange = 0.05;
    }

    if (intent.type === 'taunt' && intent.emotionalTone.humor > 0.6) {
      moraleChange = 0.08;
    }

    this.moraleStates.set(character.id, Math.min(1, Math.max(0, currentMorale + moraleChange)));
  }

  private getTacticalTargets(intent: DialogueIntent, context: CombatContext): string[] {
    // Implementation would extract specific targets from intent
    return context.characters.filter(c => c.id !== intent.target).map(c => c.id);
  }

  private calculateExpectedOutcome(intent: DialogueIntent, character: Character, context: CombatContext): string {
    return `Expected tactical advantage from ${intent.type} dialogue`;
  }

  private initializeMoraleTracking(): void {
    // Initialize morale for all characters
  }

  // Public methods for external access

  public getActiveBattleCries(characterId: string): BattleCry[] {
    return this.activeBattleCries.get(characterId) || [];
  }

  public getTacticalCommunications(): TacticalCommunication[] {
    return this.tacticalCommunications;
  }

  public getMorale(characterId: string): number {
    return this.moraleStates.get(characterId) || 0.5;
  }

  public addDialogueToHistory(characterId: string, intent: DialogueIntent): void {
    if (!this.dialogueHistory.has(characterId)) {
      this.dialogueHistory.set(characterId, []);
    }

    const history = this.dialogueHistory.get(characterId)!;
    history.push(intent);

    // Keep only last 10 intents
    if (history.length > 10) {
      history.shift();
    }
  }
}