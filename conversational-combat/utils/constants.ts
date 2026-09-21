/**
 * Constants and configuration for the Conversational Combat System
 */

// Dialogue intent patterns
export const DIALOGUE_PATTERNS = {
  // Attack patterns
  ATTACK: [
    /(\battack\b|\bstrike\b|\bhit\b|\bslash\b|\bstab\b|\bshoot\b|\bcharge\b)/i,
    /(\bi'll\b|\bi am\b|\bgoing to\b).*(\battack\b|\bhit\b|\bstrike\b)/i,
    /(\btake\b|\bdeal\b|\binflict\b).*(\bdamage\b)/i,
    /(\bunleash\b|\bbring\b|\bdeliver\b).*(\bpain\b|\bwrath\b|\bfury\b)/i
  ],

  // Intimidation patterns
  INTIMIDATION: [
    /(\bfear\b|\bafraid\b|\bterrified\b|\btremble\b)/i,
    /(\bthreat\b|\bthreaten\b|\bwarn\b|\bdare\b)/i,
    /(\bknow\b|\bthink\b|\brealize\b).*(\bwho\b|\bwhat\b).*(\bdealing\b|\bfighting\b)/i,
    /(\bface\b|\bmeet\b|\bencounter\b).*(\bdoom\b|\bdeath\b|\bend\b)/i
  ],

  // Taunt patterns
  TAUNT: [
    /(\bfool\b|\bidiot\b|\bweak\b|\bpathetic\b|\bcoward\b)/i,
    /(\bcan't\b|\bnever\b|\bwill\b|\bwon't\b).*(\bwin\b|\bsucceed\b|\bsurvive\b)/i,
    /(\bis\b|\bare\b|\bwas\b|\bwere\b).*(\bnothing\b|\buseless\b|\bworthless\b)/i,
    /(\bcome\b|\btry\b|\bshow\b).*(\bwhat\b).*(\bgot\b|\bhave\b)/i
  ],

  // Persuasion patterns
  PERSUASION: [
    /(\bplease\b|\bkindly\b|\bgently\b|\bpeacefully\b)/i,
    /(\breconsider\b|\bthink\b|\bunderstand\b|\brealize\b)/i,
    /(\bbetter\b|\bsafer\b|\bwise\b|\bsmart\b).*(\bway\b|\bchoice\b)/i,
    /(\bjoin\b|\bally\b|\bfriend\b|\btogether\b)/i
  ],

  // Deception patterns
  DECEPTION: [
    /(\btrick\b|\bfool\b|\bdeceive\b|\blie\b)/i,
    /(\believe\b|\bthink\b|\bassume\b).*(\bwrong\b|\bmistake\b)/i,
    /(\bsecret\b|\bhidden\b|\bunseen\b)/i,
    /(\bnot\b|\bnever\b).*(\bwhat\b).*(\bseems\b|\bappears\b)/i
  ],

  // Defense patterns
  DEFENSE: [
    /(\bblock\b|\bparry\b|\bdodge\b|\bdefend\b)/i,
    /(\bprotect\b|\bguard\b|\bshield\b)/i,
    /(\bhold\b|\bstand\b|\bbrace\b)/i,
    /(\bcan't\b|\bwon't\b).*(\bhit\b|\btouch\b)/i
  ],

  // Buff/Support patterns
  BUFF: [
    /(\bhelp\b|\baid\b|\bsupport\b|\bbolster\b)/i,
    /(\btogether\b|\bunited\b|\bcombined\b)/i,
    /(\bstrength\b|\bpower\b|\bmight\b).*(\bgrow\b|\bincrease\b)/i,
    /(\bbless\b|\bfavor\b|\bfortune\b)/i
  ],

  // Spell casting patterns
  SPELL: [
    /(\bcast\b|\butter\b|\bchant\b|\bspeak\b).*(\bwords\b|\bincantation\b)/i,
    /(\bmagic\b|\bspell\b|\bpower\b|\benergy\b).*(\bflow\b|\bsurge\b)/i,
    /(\barcane\b|\bdivine\b|\bnatural\b|\bprimal\b)/i,
    /(\bsummon\b|\bcall\b|\binvoke\b)/i
  ],

  // Coordination patterns
  COORDINATE: [
    /(\bteam\b|\bsquad\b|\bgroup\b|\bparty\b)/i,
    /(\btogether\b|\bcoordinated\b|\bsynchronized\b)/i,
    /(\bflank\b|\bsurround\b|\bpinch\b)/i,
    /(\bready\b|\bprepared\b|\bset\b)/i
  ]
};

// Emotional keywords
export const EMOTIONAL_KEYWORDS = {
  anger: ['fury', 'rage', 'angry', 'mad', 'enraged', 'wrath', 'vengeance', 'hate'],
  confidence: ['confident', 'sure', 'certain', 'ready', 'prepared', 'capable', 'strong', 'mighty'],
  fear: ['afraid', 'scared', 'terrified', 'frightened', 'worried', 'anxious', 'nervous'],
  humor: ['funny', 'laugh', 'joke', 'mock', 'taunt', 'sarcasm', 'wit', 'clever'],
  seriousness: ['serious', 'focused', 'determined', 'committed', 'solemn', 'grave', 'urgent'],
  desperation: ['desperate', 'urgent', 'critical', 'hopeless', 'doomed', 'final', 'last chance']
};

// Combat action mappings
export const ACTION_MAPPINGS = {
  'attack': {
    primary: 'weapon_attack',
    secondary: 'damage',
    resourceCost: { type: 'action', amount: 1 }
  },
  'spell': {
    primary: 'spell_cast',
    secondary: 'effect',
    resourceCost: { type: 'action', amount: 1 }
  },
  'defend': {
    primary: 'skill_check',
    secondary: 'defense',
    resourceCost: { type: 'action', amount: 1 }
  },
  'buff': {
    primary: 'spell_cast',
    secondary: 'healing',
    resourceCost: { type: 'bonus_action', amount: 1 }
  },
  'taunt': {
    primary: 'skill_check',
    secondary: 'debuff',
    resourceCost: { type: 'bonus_action', amount: 1 }
  }
};

// Mechanical bonuses from dialogue types
export const DIALOGUE_BONUSES = {
  intimidation: {
    advantage: ['attack', 'intimidation'],
    bonus: { type: 'bonus', value: 2, appliesTo: ['damage'] },
    duration: 1
  },
  taunt: {
    disadvantage: ['enemy_attack'],
    bonus: { type: 'bonus', value: 1, appliesTo: ['enemy_save'] },
    duration: 1
  },
  persuasion: {
    advantage: ['persuasion', 'deception'],
    bonus: { type: 'bonus', value: 1, appliesTo: ['morale'] },
    duration: 3
  },
  deception: {
    advantage: ['attack', 'stealth'],
    bonus: { type: 'bonus', value: 2, appliesTo: ['surprise'] },
    duration: 1
  },
  coordination: {
    bonus: { type: 'bonus', value: 1, appliesTo: ['ally_attack', 'ally_save'] },
    duration: 1
  },
  inspiration: {
    inspiration: true,
    bonus: { type: 'inspiration', value: 1, appliesTo: ['all'] },
    duration: 0
  }
};

// Damage types from dialogue
export const DIALOGUE_DAMAGE_TYPES = {
  'fire': ['burn', 'flame', 'scorch', 'ignite', 'inferno', 'blaze'],
  'cold': ['freeze', 'ice', 'frost', 'chill', 'winter', 'arctic'],
  'lightning': ['shock', 'bolt', 'thunder', 'storm', 'electric'],
  'poison': ['venom', 'toxin', 'corrupt', 'poison', 'disease'],
  'psychic': ['mind', 'psychic', 'mental', 'terror', 'fear'],
  'radiant': ['light', 'holy', 'divine', 'blessed', 'heavenly'],
  'necrotic': ['death', 'undead', 'dark', 'shadow', 'soul'],
  'force': ['force', 'push', 'telekinesis', 'magic'],
  'thunder': ['thunder', 'sound', 'blast', 'explosion'],
  'acid': ['acid', 'corrode', 'dissolve', 'melt']
};

// Character voice patterns
export const VOICE_PATTERNS = {
  formal: {
    vocabulary: ['indeed', 'certainly', 'perhaps', 'therefore', 'furthermore'],
    sentenceStructure: 'complex',
    formality: 0.9
  },
  casual: {
    vocabulary: ['hey', 'yeah', 'cool', 'nah', 'gonna'],
    sentenceStructure: 'simple',
    formality: 0.3
  },
  aggressive: {
    vocabulary: ['kill', 'destroy', 'crush', 'smash', 'annihilate'],
    sentenceStructure: 'fragmented',
    formality: 0.1
  },
  poetic: {
    vocabulary: ['whisper', 'dance', 'blossom', 'cascade', 'serenade'],
    sentenceStructure: 'flowery',
    formality: 0.7
  },
  technical: {
    vocabulary: ['analyze', 'calculate', 'execute', 'implement', 'optimize'],
    sentenceStructure: 'complex',
    formality: 0.8
  },
  simple: {
    vocabulary: ['hit', 'go', 'stop', 'help', 'fight'],
    sentenceStructure: 'simple',
    formality: 0.2
  }
};

// Narrative templates
export const NARRATIVE_TEMPLATES = {
  attack_start: [
    "{character} {verb} with {intensity}, {dialogue}",
    "With a {adjective} {noun}, {character} {action} and {dialogue}",
    "{dialogue}, {character} {verb} {target} with {weapon}"
  ],
  successful_hit: [
    "{dialogue} as the attack {result}",
    "The {weapon} {result}, {character} {dialogue}",
    "{dialogue} while {weapon} {result} the {target}"
  ],
  critical_hit: [
    "{dialogue} as the attack strikes true with devastating force!",
    "A perfect strike! {dialogue} as {weapon} {result}",
    "{dialogue} and the {weapon} {result} with exceptional power!"
  ],
  miss: [
    "{dialogue} but the attack goes wide",
    "Despite {dialogue}, the attack misses",
    "{dialogue} as {weapon} {result} uselessly"
  ],
  defense: [
    "{dialogue} while {character} {defense_action}",
    "With {dialogue}, {character} {defense_action}",
    "{character} {dialogue} and {defense_action}"
  ],
  spell_cast: [
    "{dialogue} as {spell_energy} {form_around_character}",
    "Magic {verb} as {character} {dialogue}",
    "{dialogue} and {spell_effect} {result}"
  ],
  dramatic_moment: [
    "{dialogue} as {dramatic_event}",
    "In this {moment_type}, {character} {dialogue}",
    "{dialogue} while {dramatic_description}"
  ]
};

// Combat intensities
export const COMBAT_INTENSITIES = {
  calm: { threshold: 0.2, speed: 1, description: 'measured' },
  tactical: { threshold: 0.4, speed: 1.2, description: 'focused' },
  intense: { threshold: 0.6, speed: 1.5, description: 'furious' },
  chaotic: { threshold: 0.8, speed: 2, description: 'frantic' },
  desperate: { threshold: 1.0, speed: 2.5, description: 'frantic and urgent' }
};

// AI enhancement constants
export const AI_ENHANCEMENT_SETTINGS = {
  maxChanges: 3,
  minQuality: 0.7,
  minCharacterMatch: 0.6,
  creativityLevel: 0.5,
  formalityRange: [0.3, 0.8],
  maxLengthIncrease: 1.5,
  maxLengthDecrease: 0.7
};

// Tactical communication patterns
export const TACTICAL_PATTERNS = {
  coordinate: [
    'on my mark', 'ready when you are', 'let\'s synchronize', 'count to three',
    'follow my lead', 'work together', 'team up on', 'focus fire on'
  ],
  warn: [
    'watch out', 'be careful', 'incoming', 'look out', 'danger', 'alert',
    'heads up', 'warning', 'caution'
  ],
  request: [
    'help me', 'cover me', 'back me up', 'support', 'assist', 'aid',
    'need help', 'reinforcement needed'
  ],
  command: [
    'attack now', 'defend this position', 'hold the line', 'retreat', 'advance',
    'fall back', 'take cover', 'focus target'
  ],
  suggest: [
    'maybe we should', 'what if we', 'how about', 'consider', 'perhaps',
    'I think we should', 'it might be wise to'
  ]
};

// Battle cry templates
export const BATTLE_CRY_TEMPLATES = {
  warrior: [
    'For honor and glory!',
    'By the blade, I strike!',
    'None shall stand before me!',
    'Blood and thunder!',
    'Victory or death!'
  ],
  mage: [
    'Arcane power, heed my call!',
    'The weave bends to my will!',
    'Magic flows through my veins!',
    'By the ancient runes!',
    'Power of the cosmos, unleashed!'
  ],
  rogue: [
    'Shadow is my ally!',
    'Strike from the darkness!',
    'Silent but deadly!',
    'Quick as a whisper!',
    'One strike, one kill!'
  ],
  cleric: [
    'Divine light, guide my hand!',
    'By the gods, I prevail!',
    'Holy power, smite the wicked!',
    'Justice shall be served!',
    'Blessed are the righteous!'
  ],
  ranger: [
    'Nature\'s wrath, unleashed!',
    'Hunter\'s instinct, never fails!',
    'One with the wild!',
    'Track and destroy!',
    'Forest fury, strike true!'
  ]
};

// Default configurations
export const DEFAULT_CONFIG = {
  dialogueProcessing: {
    enableIntentExtraction: true,
    enableEmotionalAnalysis: true,
    enableMechanicalConversion: true,
    confidenceThreshold: 0.6,
    maxDialogueLength: 500
  },
  narrativeGeneration: {
    enableCinematicDescriptions: true,
    enableCharacterVoice: true,
    enableEnvironmentalIntegration: true,
    detailLevel: 'medium',
    paceAdaptation: true
  },
  aiEnhancement: {
    enableRealTimePolishing: true,
    enableCharacterConsistency: true,
    enableTacticalSuggestions: true,
    creativityLevel: 0.5,
    responseTime: 'fast'
  },
  combatIntegration: {
    enableDialogueBonuses: true,
    enableBattleCries: true,
    enableTacticalCommunication: true,
    enableMoraleEffects: true,
    enableTeamSynergy: true
  }
};