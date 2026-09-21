/**
 * Dialogue-Combat Integration System
 * Bridges dialogue mechanics with core D&D 5e combat rules and state management
 */

import {
  CombatDialogue,
  DialogueMechanics,
  CombatContext,
  Character,
  CombatEvent,
  DialogueEffect,
  MechanicalEffect,
  CombatAction,
  Position
} from '../types';

export class DialogueCombatIntegration {
  private combatState: CombatContext;
  private activeEffects: Map<string, DialogueEffect[]> = new Map();
  private eventHistory: CombatEvent[] = [];
  private reactionQueue: ReactionAction[] = [];
  private triggerListeners: Map<string, TriggerCallback[]> = new Map();

  constructor(initialContext: CombatContext) {
    this.combatState = initialContext;
    this.initializeCombatListeners();
  }

  /**
   * Process dialogue through the full combat integration pipeline
   */
  public async processDialogueInCombat(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics
  ): Promise<CombatEvent[]> {
    const events: CombatEvent[] = [];

    // Validate dialogue in current combat context
    if (!this.validateDialogueInContext(dialogue)) {
      throw new Error('Dialogue not valid in current combat context');
    }

    // Create dialogue event
    const dialogueEvent = this.createDialogueEvent(dialogue);
    events.push(dialogueEvent);

    // Process combat action
    const actionEvents = await this.processCombatAction(dialogue, mechanics);
    events.push(...actionEvents);

    // Apply mechanical effects
    const effectEvents = this.applyMechanicalEffects(dialogue, mechanics);
    events.push(...effectEvents);

    // Process reactions
    const reactionEvents = this.processReactions(dialogue, mechanics);
    events.push(...reactionEvents);

    // Update combat state
    this.updateCombatState(dialogue, mechanics, events);

    // Store events
    this.eventHistory.push(...events);

    return events;
  }

  /**
   * Validate that dialogue can be used in current context
   */
  private validateDialogueInContext(dialogue: CombatDialogue): boolean {
    // Check if it's the character's turn
    if (!this.isCharacterTurn(dialogue.characterId)) {
      return false;
    }

    // Check if character has required resources
    if (!this.hasRequiredResources(dialogue)) {
      return false;
    }

    // Check if character can act (not incapacitated, etc.)
    if (!this.canCharacterAct(dialogue.characterId)) {
      return false;
    }

    return true;
  }

  /**
   * Process the combat action derived from dialogue
   */
  private async processCombatAction(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics
  ): Promise<CombatEvent[]> {
    const events: CombatEvent[] = [];
    const action = mechanics.combatAction;

    // Create action event
    const actionEvent: CombatEvent = {
      id: this.generateEventId(),
      type: 'action',
      timestamp: new Date(),
      characterId: dialogue.characterId,
      data: {
        action: action,
        dialogue: dialogue.text,
        intent: dialogue.intent
      },
      narrative: []
    };

    events.push(actionEvent);

    // Execute action based on type
    switch (action.type) {
      case 'weapon_attack':
        events.push(...await this.processWeaponAttack(dialogue, mechanics));
        break;
      case 'spell_cast':
        events.push(...await this.processSpellCast(dialogue, mechanics));
        break;
      case 'skill_check':
        events.push(...await this.processSkillCheck(dialogue, mechanics));
        break;
      case 'movement':
        events.push(...await this.processMovement(dialogue, mechanics));
        break;
      case 'bonus_action':
        events.push(...await this.processBonusAction(dialogue, mechanics));
        break;
      case 'reaction':
        events.push(...await this.processReactionAction(dialogue, mechanics));
        break;
    }

    return events;
  }

  /**
   * Process weapon attack derived from dialogue
   */
  private async processWeaponAttack(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics
  ): Promise<CombatEvent[]> {
    const events: CombatEvent[] = [];
    const character = this.getCharacter(dialogue.characterId);
    const target = this.getTarget(dialogue.intent?.target);
    const action = mechanics.combatAction;

    if (!target || !action.damage) {
      return events;
    }

    // Calculate attack roll with dialogue bonuses
    const attackRoll = this.calculateAttackRoll(character, target, mechanics.bonuses);
    const armorClass = target.ac;

    // Create attack roll event
    const attackEvent: CombatEvent = {
      id: this.generateEventId(),
      type: 'action',
      timestamp: new Date(),
      characterId: dialogue.characterId,
      data: {
        type: 'attack_roll',
        roll: attackRoll,
        targetAC: armorClass,
        hit: attackRoll.total >= armorClass,
        critical: attackRoll.natural20
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `${character.name} attacks with ${action.damage?.type} damage, rolling ${attackRoll.total} vs AC ${armorClass}`,
        tone: 'mechanical',
        cinematic: attackRoll.natural20
      }]
    };
    events.push(attackEvent);

    // If hit, calculate damage
    if (attackRoll.total >= armorClass) {
      const damageRoll = this.calculateDamage(character, action, mechanics.bonuses);

      const damageEvent: CombatEvent = {
        id: this.generateEventId(),
        type: 'action',
        timestamp: new Date(),
        characterId: dialogue.characterId,
        data: {
          type: 'damage',
          damage: damageRoll,
          targetId: target.id,
          damageType: action.damage.type,
          critical: attackRoll.natural20
        },
        narrative: [{
          id: this.generateNarrativeId(),
          type: 'description',
          content: `${character.name} deals ${damageRoll.total} ${action.damage.type} damage to ${target.name}${attackRoll.natural20 ? ' (CRITICAL HIT!)' : ''}`,
          tone: attackRoll.natural20 ? 'epic' : 'mechanical',
          cinematic: attackRoll.natural20
        }]
      };
      events.push(damageEvent);

      // Update target HP
      target.hp -= damageRoll.total;
    }

    return events;
  }

  /**
   * Process spell casting derived from dialogue
   */
  private async processSpellCast(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics
  ): Promise<CombatEvent[]> {
    const events: CombatEvent[] = [];
    const character = this.getCharacter(dialogue.characterId);
    const action = mechanics.combatAction;

    // Create spell casting event
    const castEvent: CombatEvent = {
      id: this.generateEventId(),
      type: 'action',
      timestamp: new Date(),
      characterId: dialogue.characterId,
      data: {
        type: 'spell_cast',
        spell: action.actionName,
        components: this.getSpellComponents(dialogue),
        concentration: this.requiresConcentration(action)
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `${character.name} casts ${action.actionName}, speaking the words: "${dialogue.text}"`,
        tone: 'magical',
        cinematic: true
      }]
    };
    events.push(castEvent);

    // Process spell effects
    if (action.effect) {
      const effectEvents = this.processSpellEffects(dialogue, action);
      events.push(...effectEvents);
    }

    if (action.save) {
      const saveEvents = this.processSavingThrows(dialogue, action);
      events.push(...saveEvents);
    }

    return events;
  }

  /**
   * Process skill checks derived from dialogue
   */
  private async processSkillCheck(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics
  ): Promise<CombatEvent[]> {
    const events: CombatEvent[] = [];
    const character = this.getCharacter(dialogue.characterId);
    const skill = this.getSkillFromIntent(dialogue.intent?.type);

    // Calculate skill check with dialogue bonuses
    const skillRoll = this.calculateSkillCheck(character, skill, mechanics.bonuses);
    const dc = this.calculateDifficultyClass(dialogue, mechanics);

    const checkEvent: CombatEvent = {
      id: this.generateEventId(),
      type: 'action',
      timestamp: new Date(),
      characterId: dialogue.characterId,
      data: {
        type: 'skill_check',
        skill: skill,
        roll: skillRoll,
        dc: dc,
        success: skillRoll.total >= dc
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `${character.name} makes a ${skill} check, rolling ${skillRoll.total} vs DC ${dc}`,
        tone: 'mechanical',
        cinematic: skillRoll.natural20
      }]
    };
    events.push(checkEvent);

    // Apply skill check effects
    if (skillRoll.total >= dc) {
      const successEvents = this.applySkillCheckSuccess(dialogue, mechanics, skillRoll);
      events.push(...successEvents);
    } else {
      const failureEvents = this.applySkillCheckFailure(dialogue, mechanics, skillRoll);
      events.push(...failureEvents);
    }

    return events;
  }

  /**
   * Apply mechanical effects from dialogue
   */
  private applyMechanicalEffects(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics
  ): CombatEvent[] {
    const events: CombatEvent[] = [];

    // Apply bonuses
    for (const bonus of mechanics.bonuses) {
      const effectEvent = this.applyBonus(dialogue.characterId, bonus);
      events.push(effectEvent);
    }

    // Apply conditions
    for (const condition of mechanics.conditions) {
      const conditionEvent = this.applyCondition(dialogue, condition);
      events.push(conditionEvent);
    }

    // Apply duration-based effects
    if (mechanics.duration > 0) {
      const durationEvent = this.applyDurationEffect(dialogue, mechanics);
      events.push(durationEvent);
    }

    return events;
  }

  /**
   * Process reactions triggered by dialogue
   */
  private processReactions(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics
  ): CombatEvent[] {
    const events: CombatEvent[] = [];

    // Check for reaction triggers
    const triggeredReactions = this.checkReactionTriggers(dialogue, mechanics);

    for (const reaction of triggeredReactions) {
      const reactionEvent = this.executeReaction(reaction, dialogue);
      events.push(reactionEvent);
    }

    return events;
  }

  /**
   * Update combat state after dialogue processing
   */
  private updateCombatState(
    dialogue: CombatDialogue,
    mechanics: DialogueMechanics,
    events: CombatEvent[]
  ): void {
    // Update turn order
    this.updateTurnOrder(dialogue.characterId);

    // Update initiative if necessary
    this.updateInitiative(dialogue, events);

    // Check combat end conditions
    this.checkCombatEndConditions();

    // Update environmental state
    this.updateEnvironmentalState(dialogue, mechanics);
  }

  // Helper methods for combat mechanics

  private isCharacterTurn(characterId: string): boolean {
    return this.combatState.state.activeTurns.includes(characterId);
  }

  private hasRequiredResources(dialogue: CombatDialogue): boolean {
    const character = this.getCharacter(dialogue.characterId);

    // Check action economy
    const hasAction = character.position !== undefined; // Simplified check
    const hasBonusAction = true; // Simplified check
    const hasReaction = true; // Simplified check

    return hasAction; // Simplified for now
  }

  private canCharacterAct(characterId: string): boolean {
    const character = this.getCharacter(characterId);

    // Check for incapacitating conditions
    const incapacitatingConditions = ['Incapacitated', 'Stunned', 'Unconscious', 'Petrified'];
    return !incapacitatingConditions.some(condition =>
      character.conditions.some(c => c.name === condition)
    );
  }

  private getCharacter(characterId: string): Character {
    const character = this.combatState.characters.find(c => c.id === characterId);
    if (!character) {
      throw new Error(`Character ${characterId} not found in combat state`);
    }
    return character;
  }

  private getTarget(targetId?: string): Character | undefined {
    if (!targetId) return undefined;
    return this.combatState.characters.find(c => c.id === targetId);
  }

  private calculateAttackRoll(
    attacker: Character,
    target: Character,
    bonuses: any[]
  ): { total: number; natural20: boolean; details: string[] } {
    const d20Roll = Math.floor(Math.random() * 20) + 1;
    const natural20 = d20Roll === 20;

    const proficiencyBonus = Math.floor((attacker.level - 1) / 4) + 2;
    const strengthMod = Math.floor((attacker.abilities.strength - 10) / 2);

    let total = d20Roll + proficiencyBonus + strengthMod;

    // Apply dialogue bonuses
    for (const bonus of bonuses) {
      if (bonus.type === 'bonus' && bonus.appliesTo.includes('attack')) {
        total += bonus.value;
      }
    }

    // Check for advantage
    const hasAdvantage = bonuses.some(b => b.type === 'advantage' && b.appliesTo.includes('attack'));
    if (hasAdvantage && !natural20) {
      const secondRoll = Math.floor(Math.random() * 20) + 1;
      total = Math.max(total, secondRoll + proficiencyBonus + strengthMod);
    }

    const details = [
      `d20: ${d20Roll}`,
      `Proficiency: +${proficiencyBonus}`,
      `Strength: +${strengthMod}`,
      ...bonuses.filter(b => b.appliesTo.includes('attack')).map(b => `${b.source}: +${b.value}`)
    ];

    return { total, natural20, details };
  }

  private calculateDamage(
    attacker: Character,
    action: CombatAction,
    bonuses: any[]
  ): { total: number; details: string[] } {
    if (!action.damage) return { total: 0, details: [] };

    const baseDamage = action.damage.amount || 4;
    const strengthMod = Math.floor((attacker.abilities.strength - 10) / 2);

    let total = baseDamage + strengthMod + (action.damage.bonus || 0);

    // Apply dialogue bonuses
    for (const bonus of bonuses) {
      if (bonus.type === 'bonus' && bonus.appliesTo.includes('damage')) {
        total += bonus.value;
      }
    }

    // Double damage for critical hits
    if (action.damage.critical) {
      total *= 2;
    }

    const details = [
      `Base: ${baseDamage}`,
      `Strength: +${strengthMod}`,
      `Bonus: +${action.damage.bonus || 0}`,
      ...bonuses.filter(b => b.appliesTo.includes('damage')).map(b => `${b.source}: +${b.value}`)
    ];

    return { total, details };
  }

  private calculateSkillCheck(
    character: Character,
    skill: string,
    bonuses: any[]
  ): { total: number; natural20: boolean; details: string[] } {
    const d20Roll = Math.floor(Math.random() * 20) + 1;
    const natural20 = d20Roll === 20;

    const proficiencyBonus = Math.floor((character.level - 1) / 4) + 2;
    const skillMod = (character.skills as any)[skill.toLowerCase()] || 0;

    let total = d20Roll + proficiencyBonus + skillMod;

    // Apply dialogue bonuses
    for (const bonus of bonuses) {
      if (bonus.appliesTo.includes(skill)) {
        total += bonus.value;
      }
    }

    const details = [
      `d20: ${d20Roll}`,
      `Proficiency: +${proficiencyBonus}`,
      `Skill: +${skillMod}`,
      ...bonuses.filter(b => b.appliesTo.includes(skill)).map(b => `${b.source}: +${b.value}`)
    ];

    return { total, natural20, details };
  }

  private calculateDifficultyClass(dialogue: CombatDialogue, mechanics: DialogueMechanics): number {
    // Base DC
    let dc = 13;

    // Adjust based on strategic value
    if (dialogue.intent) {
      dc += Math.floor(dialogue.intent.strategicValue * 2);
    }

    // Adjust based on target strength
    const target = this.getTarget(dialogue.intent?.target);
    if (target) {
      dc += Math.floor(target.level / 2);
    }

    return dc;
  }

  private getSkillFromIntent(intentType?: string): string {
    const skillMap = {
      'intimidate': 'intimidation',
      'persuade': 'persuasion',
      'deceive': 'deception',
      'coordinate': 'insight',
      'taunt': 'performance'
    };

    return skillMap[intentType as keyof typeof skillMap] || 'athletics';
  }

  private applyBonus(characterId: string, bonus: any): CombatEvent {
    return {
      id: this.generateEventId(),
      type: 'effect',
      timestamp: new Date(),
      characterId,
      data: {
        type: 'bonus_applied',
        bonus: bonus
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `Applied ${bonus.type} ${bonus.value} to ${bonus.appliesTo.join(', ')}`,
        tone: 'mechanical',
        cinematic: false
      }]
    };
  }

  private applyCondition(dialogue: CombatDialogue, conditionName: string): CombatEvent {
    const targetId = dialogue.intent?.target;

    return {
      id: this.generateEventId(),
      type: 'effect',
      timestamp: new Date(),
      characterId: targetId || dialogue.characterId,
      data: {
        type: 'condition_applied',
        condition: conditionName,
        source: 'dialogue'
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `${this.getCharacter(targetId || dialogue.characterId).name} is now ${conditionName}`,
        tone: 'mechanical',
        cinematic: false
      }]
    };
  }

  private applyDurationEffect(dialogue: CombatDialogue, mechanics: DialogueMechanics): CombatEvent {
    const effect: DialogueEffect = {
      id: this.generateEffectId(),
      type: 'duration',
      targets: [dialogue.characterId],
      effects: mechanics.bonuses.map(b => ({
        property: b.appliesTo[0],
        operation: 'add' as const,
        value: b.value,
        duration: mechanics.duration
      })),
      narrative: dialogue.text,
      source: dialogue.id
    };

    // Store active effect
    if (!this.activeEffects.has(dialogue.characterId)) {
      this.activeEffects.set(dialogue.characterId, []);
    }
    this.activeEffects.get(dialogue.characterId)!.push(effect);

    return {
      id: this.generateEventId(),
      type: 'effect',
      timestamp: new Date(),
      characterId: dialogue.characterId,
      data: {
        type: 'duration_effect_applied',
        effect: effect
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `Duration effect applied: ${dialogue.text}`,
        tone: 'mechanical',
        cinematic: false
      }]
    };
  }

  private checkReactionTriggers(dialogue: CombatDialogue, mechanics: DialogueMechanics): ReactionAction[] {
    const triggeredReactions: ReactionAction[] = [];

    // Check for attack reactions
    if (mechanics.combatAction.type === 'weapon_attack') {
      triggeredReactions.push(...this.getAttackReactions(dialogue));
    }

    // Check for spell reactions
    if (mechanics.combatAction.type === 'spell_cast') {
      triggeredReactions.push(...this.getSpellReactions(dialogue));
    }

    return triggeredReactions;
  }

  private getAttackReactions(dialogue: CombatDialogue): ReactionAction[] {
    const reactions: ReactionAction[] = [];

    // Check for Shield spell
    const target = this.getTarget(dialogue.intent?.target);
    if (target && this.canCastShield(target)) {
      reactions.push({
        characterId: target.id,
        type: 'shield_spell',
        trigger: 'being_attacked',
        source: dialogue.id
      });
    }

    return reactions;
  }

  private getSpellReactions(dialogue: CombatDialogue): ReactionAction[] {
    // Check for Counterspell reactions
    return [];
  }

  private canCastShield(character: Character): boolean {
    return character.spells.some(s => s.name.toLowerCase() === 'shield');
  }

  private executeReaction(reaction: ReactionAction, triggerDialogue: CombatDialogue): CombatEvent {
    const reactor = this.getCharacter(reaction.characterId);

    return {
      id: this.generateEventId(),
      type: 'effect',
      timestamp: new Date(),
      characterId: reaction.characterId,
      data: {
        type: 'reaction_executed',
        reaction: reaction,
        trigger: triggerDialogue.id
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `${reactor.name} uses ${reaction.type} in response to ${triggerDialogue.text}`,
        tone: 'mechanical',
        cinematic: true
      }]
    };
  }

  private processSpellEffects(dialogue: CombatDialogue, action: CombatAction): CombatEvent[] {
    // Implementation for processing ongoing spell effects
    return [];
  }

  private processSavingThrows(dialogue: CombatDialogue, action: CombatAction): CombatEvent[] {
    const events: CombatEvent[] = [];

    if (!action.save) return events;

    const target = this.getTarget(dialogue.intent?.target);
    if (!target) return events;

    const saveRoll = this.calculateSavingThrow(target, action.save.ability);

    const saveEvent: CombatEvent = {
      id: this.generateEventId(),
      type: 'effect',
      timestamp: new Date(),
      characterId: target.id,
      data: {
        type: 'saving_throw',
        ability: action.save.ability,
        dc: action.save.dc,
        roll: saveRoll,
        success: saveRoll.total >= action.save.dc
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'description',
        content: `${target.name} makes a ${action.save.ability} save, rolling ${saveRoll.total} vs DC ${action.save.dc}`,
        tone: 'mechanical',
        cinematic: saveRoll.natural20 || saveRoll.total >= action.save.dc
      }]
    };

    events.push(saveEvent);

    return events;
  }

  private calculateSavingThrow(character: Character, ability: string): { total: number; natural20: boolean } {
    const d20Roll = Math.floor(Math.random() * 20) + 1;
    const natural20 = d20Roll === 20;

    const abilityScore = (character.abilities as any)[ability.toLowerCase()] || 10;
    const abilityMod = Math.floor((abilityScore - 10) / 2);
    const proficiencyBonus = Math.floor((character.level - 1) / 4) + 2;

    const total = d20Roll + abilityMod + proficiencyBonus;

    return { total, natural20 };
  }

  private applySkillCheckSuccess(dialogue: CombatDialogue, mechanics: DialogueMechanics, roll: any): CombatEvent[] {
    // Implementation for successful skill check effects
    return [];
  }

  private applySkillCheckFailure(dialogue: CombatDialogue, mechanics: DialogueMechanics, roll: any): CombatEvent[] {
    // Implementation for failed skill check effects
    return [];
  }

  private updateTurnOrder(characterId: string): void {
    const index = this.combatState.state.activeTurns.indexOf(characterId);
    if (index > -1) {
      this.combatState.state.activeTurns.splice(index, 1);
    }
  }

  private updateInitiative(dialogue: CombatDialogue, events: CombatEvent[]): void {
    // Update initiative based on events
  }

  private checkCombatEndConditions(): void {
    const livingCharacters = this.combatState.characters.filter(c => c.hp > 0);

    if (livingCharacters.length <= 1) {
      this.combatState.state.phase = 'ending';
    }
  }

  private updateEnvironmentalState(dialogue: CombatDialogue, mechanics: DialogueMechanics): void {
    // Update environment based on dialogue effects
  }

  private initializeCombatListeners(): void {
    // Initialize trigger listeners
  }

  private getSpellComponents(dialogue: CombatDialogue): string[] {
    return ['V']; // Dialogue provides verbal components
  }

  private requiresConcentration(action: CombatAction): boolean {
    return action.effect?.duration !== undefined && action.effect.duration > 0;
  }

  private createDialogueEvent(dialogue: CombatDialogue): CombatEvent {
    return {
      id: this.generateEventId(),
      type: 'dialogue',
      timestamp: new Date(),
      characterId: dialogue.characterId,
      data: {
        dialogue: dialogue,
        intent: dialogue.intent
      },
      narrative: [{
        id: this.generateNarrativeId(),
        type: 'dialogue',
        content: dialogue.text,
        speaker: this.getCharacter(dialogue.characterId).name,
        tone: 'dialogue',
        cinematic: false
      }]
    };
  }

  // ID generation methods
  private generateEventId(): string {
    return `event_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateNarrativeId(): string {
    return `narrative_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateEffectId(): string {
    return `effect_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Public API methods
  public getCombatState(): CombatContext {
    return this.combatState;
  }

  public getEventHistory(): CombatEvent[] {
    return this.eventHistory;
  }

  public getActiveEffects(characterId?: string): DialogueEffect[] {
    if (characterId) {
      return this.activeEffects.get(characterId) || [];
    }

    const allEffects: DialogueEffect[] = [];
    for (const effects of this.activeEffects.values()) {
      allEffects.push(...effects);
    }
    return allEffects;
  }

  public updateCombatState(newState: CombatContext): void {
    this.combatState = newState;
  }
}

interface ReactionAction {
  characterId: string;
  type: string;
  trigger: string;
  source: string;
}

interface TriggerCallback {
  trigger: string;
  callback: (event: CombatEvent) => void;
}