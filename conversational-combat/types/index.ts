/**
 * Core type definitions for the Conversational Combat System
 */

export interface CombatDialogue {
  id: string;
  characterId: string;
  text: string;
  timestamp: Date;
  combatContext: CombatContext;
  intent?: DialogueIntent;
  mechanics?: DialogueMechanics;
}

export interface DialogueIntent {
  type: 'attack' | 'defend' | 'buff' | 'debuff' | 'taunt' | 'intimidate' | 'persuade' | 'deceive' | 'coordinate' | 'spell';
  target?: string;
  action?: string;
  flavor?: string;
  confidence: number;
  emotionalTone: EmotionalTone;
  strategicValue: number;
}

export interface EmotionalTone {
  anger: number;       // 0-1
  confidence: number;  // 0-1
  fear: number;        // 0-1
  humor: number;       // 0-1
  seriousness: number; // 0-1
  desperation: number; // 0-1
}

export interface DialogueMechanics {
  combatAction: CombatAction;
  bonuses: MechanicalBonus[];
  resourceCosts: ResourceCost[];
  duration: number;
  conditions: string[];
  synergies: string[];
}

export interface CombatAction {
  type: 'weapon_attack' | 'spell_cast' | 'skill_check' | 'movement' | 'bonus_action' | 'reaction';
  actionName: string;
  damage?: DamageInfo;
  healing?: HealingInfo;
  save?: SaveInfo;
  effect?: EffectInfo;
}

export interface MechanicalBonus {
  type: 'advantage' | 'disadvantage' | 'bonus' | 'penalty' | 'critical' | 'inspiration';
  value: number;
  source: string;
  appliesTo: string[];
  duration: number;
}

export interface DamageInfo {
  amount: number;
  type: string;
  bonus: number;
  critical: boolean;
}

export interface HealingInfo {
  amount: number;
  type: 'temp' | 'regular';
  source: string;
}

export interface SaveInfo {
  ability: string;
  dc: number;
  effectOnFail: string;
  effectOnSuccess: string;
}

export interface EffectInfo {
  name: string;
  duration: number;
  description: string;
}

export interface ResourceCost {
  type: 'action' | 'bonus_action' | 'reaction' | 'spell_slot' | 'ki' | 'rage' | 'superiority_dice';
  amount: number;
  source?: string;
}

export interface CombatContext {
  round: number;
  turn: number;
  characters: Character[];
  environment: Environment;
  state: CombatState;
  weather?: WeatherCondition;
  lighting: LightingCondition;
}

export interface Character {
  id: string;
  name: string;
  class: string;
  level: number;
  hp: number;
  maxHp: number;
  ac: number;
  speed: number;
  abilities: AbilityScores;
  skills: SkillProficiencies;
  equipment: Equipment[];
  spells: Spell[];
  conditions: Condition[];
  position: Position;
  personality: Personality;
  voice: VoicePattern;
}

export interface AbilityScores {
  strength: number;
  dexterity: number;
  constitution: number;
  intelligence: number;
  wisdom: number;
  charisma: number;
}

export interface SkillProficiencies {
  athletics: number;
  acrobatics: number;
  sleightOfHand: number;
  stealth: number;
  arcana: number;
  history: number;
  investigation: number;
  nature: number;
  religion: number;
  animalHandling: number;
  insight: number;
  medicine: number;
  perception: number;
  survival: number;
  deception: number;
  intimidation: number;
  performance: number;
  persuasion: number;
}

export interface Personality {
  traits: string[];
  ideals: string[];
  bonds: string[];
  flaws: string[];
  speechPatterns: string[];
  emotionalTriggers: string[];
}

export interface VoicePattern {
  vocabulary: 'formal' | 'casual' | 'aggressive' | 'poetic' | 'technical' | 'simple';
  sentenceStructure: 'complex' | 'simple' | 'fragmented' | 'flowery';
  commonPhrases: string[];
  accents: string[];
  tics: string[];
}

export interface Environment {
  name: string;
  description: string;
  features: EnvironmentFeature[];
  hazards: Hazard[];
  opportunities: Opportunity[];
}

export interface EnvironmentFeature {
  name: string;
  type: 'cover' | 'terrain' | 'obstacle' | 'interactive' | 'decoration';
  description: string;
  mechanics?: string;
}

export interface Hazard {
  name: string;
  type: 'damage' | 'condition' | 'movement' | 'visibility';
  description: string;
  effect: string;
}

export interface Opportunity {
  name: string;
  type: 'attack' | 'defense' | 'utility' | 'narrative';
  description: string;
  requirements: string[];
}

export interface Position {
  x: number;
  y: number;
  z: number;
  facing: string;
  cover: CoverType;
}

export type CoverType = 'none' | 'half' | 'three_quarters' | 'full';

export interface Condition {
  name: string;
  duration: number;
  source: string;
  effects: string[];
}

export interface Equipment {
  id: string;
  name: string;
  type: 'weapon' | 'armor' | 'shield' | 'tool' | 'consumable' | 'trinket';
  properties: string[];
  damage?: string;
  magical: boolean;
  description: string;
}

export interface Spell {
  id: string;
  name: string;
  level: number;
  school: string;
  castingTime: string;
  range: string;
  components: string;
  duration: string;
  description: string;
}

export interface CombatState {
  phase: 'pre_combat' | 'surprise' | 'initiative' | 'combat' | 'ending' | 'post_combat';
  activeTurns: string[];
  preparedActions: PreparedAction[];
  reactions: Reaction[];
  morale: MoraleState;
}

export interface PreparedAction {
  characterId: string;
  trigger: string;
  action: string;
  description: string;
}

export interface Reaction {
  characterId: string;
  trigger: string;
  action: string;
  used: boolean;
}

export interface MoraleState {
  allies: number;
  enemies: number;
  confidence: number;
  desperation: number;
}

export type WeatherCondition = 'clear' | 'rain' | 'storm' | 'fog' | 'wind' | 'snow' | 'extreme';

export type LightingCondition = 'bright' | 'dim' | 'darkness' | 'magical_darkness';

export interface DialogueEffect {
  id: string;
  type: 'immediate' | 'duration' | 'permanent';
  targets: string[];
  effects: MechanicalEffect[];
  narrative: string;
  source: string;
}

export interface MechanicalEffect {
  property: string;
  operation: 'add' | 'multiply' | 'set' | 'advantage' | 'disadvantage';
  value: number | boolean;
  duration?: number;
}

export interface NarrativeElement {
  id: string;
  type: 'description' | 'dialogue' | 'action' | 'effect' | 'transition';
  content: string;
  speaker?: string;
  tone: string;
  cinematic: boolean;
}

export interface CombatEvent {
  id: string;
  type: 'dialogue' | 'action' | 'effect' | 'turn_start' | 'turn_end' | 'round_start' | 'round_end';
  timestamp: Date;
  characterId?: string;
  data: any;
  narrative: NarrativeElement[];
}

export interface ConversationFlow {
  participants: string[];
  currentSpeaker: string;
  context: ConversationContext;
  history: DialogueEntry[];
  pendingActions: PendingAction[];
}

export interface ConversationContext {
  topic: string;
  tension: number;
  urgency: number;
  formality: number;
  hostility: number;
}

export interface DialogueEntry {
  id: string;
  speaker: string;
  text: string;
  intent: DialogueIntent;
  response: string;
  timestamp: Date;
}

export interface PendingAction {
  type: string;
  requirements: string[];
  description: string;
  priority: number;
}

// Enhanced AI interfaces
export interface AIDialogueEnhancement {
  originalText: string;
  enhancedText: string;
  changes: DialogueChange[];
  quality: number;
  characterMatch: number;
}

export interface DialogueChange {
  type: 'wording' | 'tone' | 'emotion' | 'mechanics' | 'flavor';
  original: string;
  modified: string;
  reason: string;
}

export interface TacticalCommunication {
  type: 'coordinate' | 'warn' | 'request' | 'command' | 'suggest';
  priority: number;
  urgency: number;
  targets: string[];
  content: string;
  expectedOutcome: string;
}

export interface BattleCry {
  phrase: string;
  effect: BattleCryEffect;
  cooldown: number;
  uses: number;
  characterTrait: string;
}

export interface BattleCryEffect {
  type: 'buff' | 'debuff' | 'inspire' | 'fear';
  targets: 'self' | 'allies' | 'enemies' | 'all';
  range: number;
  duration: number;
  mechanicalBonus: MechanicalBonus[];
}

export interface DialogueStrategy {
  approach: 'aggressive' | 'defensive' | 'tactical' | 'inspiring' | 'deceptive';
  preferredIntents: DialogueIntent['type'][];
  emotionalProfile: EmotionalTone;
  tacticalGoals: string[];
  adaptations: string[];
}