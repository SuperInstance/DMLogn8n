/**
 * Conversational Combat System Demo
 * Showcase of revolutionary dialogue-driven combat mechanics
 */

import {
  ConversationalCombatSystem,
  CombatContext,
  Character,
  AbilityScores,
  SkillProficiencies,
  Personality,
  VoicePattern,
  Position
} from '../index';

// Sample combat characters
const createSampleCharacters = (): Character[] => {
  return [
    {
      id: 'fighter_001',
      name: 'Kaelen Stormblade',
      class: 'Fighter',
      level: 8,
      hp: 68,
      maxHp: 85,
      ac: 18,
      speed: 30,
      abilities: {
        strength: 18,
        dexterity: 14,
        constitution: 16,
        intelligence: 12,
        wisdom: 13,
        charisma: 14
      },
      skills: {
        athletics: 5,
        acrobatics: 2,
        sleightOfHand: 1,
        stealth: 2,
        arcana: 0,
        history: 1,
        investigation: 1,
        nature: 0,
        religion: 2,
        animalHandling: 1,
        insight: 1,
        medicine: 1,
        perception: 3,
        survival: 2,
        deception: 2,
        intimidation: 4,
        performance: 1,
        persuasion: 2
      },
      equipment: [
        {
          id: 'longsword_001',
          name: 'Flame-Bound Longsword +2',
          type: 'weapon',
          properties: ['versatile', 'magical'],
          damage: '1d8+3 slashing',
          magical: true,
          description: 'A longsword wreathed in eternal flames'
        }
      ],
      spells: [],
      conditions: [],
      position: { x: 10, y: 10, z: 0, facing: 'north', cover: 'none' },
      personality: {
        traits: ['Brave', 'Protective of allies', 'Honorable'],
        ideals: ['Justice', 'Honor', 'Courage'],
        bonds: ['Sworn to protect the innocent', 'Loyal to companions'],
        flaws: ['Reckless when protecting others', 'Refuses to back down'],
        speechPatterns: ['Direct', 'Commanding', 'Honest'],
        emotionalTriggers: ['Injustice', 'Threats to allies', 'Dishonor']
      },
      voice: {
        vocabulary: 'formal',
        sentenceStructure: 'complex',
        commonPhrases: ['By my honor', 'For justice', 'Stand firm'],
        accents: ['Noble bearing'],
        tics: ['Pauses for emphasis']
      }
    },
    {
      id: 'wizard_001',
      name: 'Lyra Starweaver',
      class: 'Wizard',
      level: 9,
      hp: 45,
      maxHp: 52,
      ac: 14,
      speed: 30,
      abilities: {
        strength: 10,
        dexterity: 14,
        constitution: 12,
        intelligence: 20,
        wisdom: 15,
        charisma: 12
      },
      skills: {
        athletics: 0,
        acrobatics: 2,
        sleightOfHand: 2,
        stealth: 2,
        arcana: 8,
        history: 4,
        investigation: 6,
        nature: 3,
        religion: 4,
        animalHandling: 0,
        insight: 2,
        medicine: 1,
        perception: 4,
        survival: 2,
        deception: 1,
        intimidation: 0,
        performance: 1,
        persuasion: 2
      },
      equipment: [
        {
          id: 'staff_001',
          name: 'Staff of the Archmagi',
          type: 'weapon',
          properties: ['magical', 'spellcasting focus'],
          magical: true,
          description: 'An ancient staff pulsing with arcane power'
        }
      ],
      spells: [
        {
          id: 'fireball_001',
          name: 'Fireball',
          level: 3,
          school: 'Evocation',
          castingTime: '1 action',
          range: '150 feet',
          components: 'V, S, M',
          duration: 'Instantaneous',
          description: 'A brilliant streak of lightning flashes from your pointing finger'
        }
      ],
      conditions: [],
      position: { x: 8, y: 8, z: 0, facing: 'north', cover: 'half' },
      personality: {
        traits: ['Brilliant', 'Curious', 'Methodical'],
        ideals: ['Knowledge', 'Mastery of magic', 'Discovery'],
        bonds: ['Dedicated to uncovering ancient secrets', 'Protects knowledge at all costs'],
        flaws: ['Arrogant about intelligence', 'Dismissive of non-magical solutions'],
        speechPatterns: ['Precise', 'Technical', 'Explanatory'],
        emotionalTriggers: ['Challenges to knowledge', 'Destruction of lore', 'Anti-magic sentiment']
      },
      voice: {
        vocabulary: 'technical',
        sentenceStructure: 'complex',
        commonPhrases: ['The arcane laws dictate', 'By theoretical principle', 'Consider the magical implications'],
        accents: ['Academic precision'],
        tics: ['Adjusts spectacles', 'Uses precise terminology']
      }
    },
    {
      id: 'rogue_001',
      name: 'Shadow Swiftblade',
      class: 'Rogue',
      level: 8,
      hp: 58,
      maxHp: 71,
      ac: 16,
      speed: 35,
      abilities: {
        strength: 12,
        dexterity: 18,
        constitution: 14,
        intelligence: 14,
        wisdom: 12,
        charisma: 15
      },
      skills: {
        athletics: 1,
        acrobatics: 6,
        sleightOfHand: 6,
        stealth: 8,
        arcana: 2,
        history: 1,
        investigation: 4,
        nature: 1,
        religion: 1,
        animalHandling: 1,
        insight: 3,
        medicine: 1,
        perception: 5,
        survival: 3,
        deception: 6,
        intimidation: 4,
        performance: 3,
        persuasion: 5
      },
      equipment: [
        {
          id: 'daggers_001',
          name: 'Shadow-Wrought Daggers +1',
          type: 'weapon',
          properties: ['finesse', 'light', 'magical'],
          damage: '1d4+4 piercing',
          magical: true,
          description: 'Daggers that seem to absorb light'
        }
      ],
      spells: [
        {
          id: 'mage_hand_001',
          name: "Mage Hand",
          level: 0,
          school: 'Conjuration',
          castingTime: '1 action',
          range: '30 feet',
          components: 'V, S',
          duration: '1 minute',
          description: 'A spectral, floating hand appears at a point you choose'
        }
      ],
      conditions: [],
      position: { x: 12, y: 9, z: 0, facing: 'east', cover: 'three_quarters' },
      personality: {
        traits: ['Witty', 'Opportunistic', 'Cunning'],
        ideals: ['Freedom', 'Personal gain', 'Clever solutions'],
        bonds: ['Loyalty to those who earned trust', 'Seeks legendary treasures'],
        flaws: ['Greedy for valuable items', 'Overconfident in skills'],
        speechPatterns: ['Sarcastic', 'Witty', 'Economical'],
        emotionalTriggers: ['Valuable treasures', 'Underestimation', 'Locked doors/chests']
      },
      voice: {
        vocabulary: 'casual',
        sentenceStructure: 'simple',
        commonPhrases: ['Watch this', 'Too easy', 'Let me handle that'],
        accents: ['Street-smart'],
        tics: ['Smirks at serious moments', 'Uses finger quotes']
      }
    },
    // Enemy characters
    {
      id: 'dragon_001',
      name: 'Inferno the Red Dragon',
      class: 'Dragon',
      level: 15,
      hp: 256,
      maxHp: 256,
      ac: 19,
      speed: 40,
      abilities: {
        strength: 27,
        dexterity: 14,
        constitution: 25,
        intelligence: 16,
        wisdom: 15,
        charisma: 23
      },
      skills: {
        athletics: 13,
        acrobatics: 7,
        sleightOfHand: 7,
        stealth: 7,
        arcana: 10,
        history: 10,
        investigation: 10,
        nature: 10,
        religion: 8,
        animalHandling: 8,
        insight: 8,
        medicine: 8,
        perception: 15,
        survival: 8,
        deception: 11,
        intimidation: 15,
        performance: 11,
        persuasion: 11
      },
      equipment: [
        {
          id: 'dragon_claws',
          name: 'Dragon Claws',
          type: 'weapon',
          properties: ['natural'],
          damage: '2d10+8 slashing',
          magical: false,
          description: 'Natural dragon weaponry'
        }
      ],
      spells: [],
      conditions: [],
      position: { x: 5, y: 15, z: 10, facing: 'south', cover: 'none' },
      personality: {
        traits: ['Arrogant', 'Territorial', 'Greedy'],
        ideals: ['Wealth', 'Power', 'Domination'],
        bonds: ['Treasure hoard', 'Mountain lair'],
        flaws: ['Underestimates mortals', 'Obsessed with gold'],
        speechPatterns: ['Imperious', 'Threatening', 'Grandiose'],
        emotionalTriggers: ['Threats to treasure', 'Challenges to authority', 'Mortal insolence']
      },
      voice: {
        vocabulary: 'aggressive',
        sentenceStructure: 'complex',
        commonPhrases: ['Foolish mortals', 'BURN!', 'My treasure'],
        accents: ['Dragon's rumble'],
        tics: ['Smoke from nostrils', 'Deep resonant voice']
      }
    }
  ];
};

// Create sample combat context
const createCombatContext = (): CombatContext => {
  const characters = createSampleCharacters();

  return {
    round: 1,
    turn: 1,
    characters,
    environment: {
      name: 'Dragon\'s Lair',
      description: 'A vast cavern filled with treasure hoards and scorched stone. The air shimmers with heat and the smell of sulfur.',
      features: [
        {
          name: 'Treasure Piles',
          type: 'interactive',
          description: 'Massive piles of gold coins and jewels provide partial cover'
        },
        {
          name: 'Lava Moat',
          type: 'hazard',
          description: 'A river of lava cuts across the chamber floor'
        },
        {
          name: 'Ceiling Stalactites',
          type: 'terrain',
          description: 'Sharp stone formations hang precariously overhead'
        }
      ],
      hazards: [
        {
          name: 'Extreme Heat',
          type: 'damage',
          description: 'The intense heat causes 1d6 fire damage per round without protection',
          effect: '1d6 fire damage per round'
        }
      ],
      opportunities: [
        {
          name: 'Ceiling Collapse',
          type: 'attack',
          description: 'Shattering stalactites can deal massive damage',
          requirements: ['Successful attack on ceiling', 'DEX save to avoid']
        }
      ]
    },
    state: {
      phase: 'combat',
      activeTurns: ['fighter_001'],
      preparedActions: [],
      reactions: [
        {
          characterId: 'wizard_001',
          trigger: 'being_attacked',
          action: 'cast Shield',
          used: false
        }
      ],
      morale: {
        allies: 0.7,
        enemies: 0.9,
        confidence: 0.6,
        desperation: 0.3
      }
    },
    lighting: 'dim'
  };
};

// Demo scenarios
class ConversationalCombatDemo {
  private system: ConversationalCombatSystem;

  constructor() {
    this.system = new ConversationalCombatSystem(createCombatContext());
  }

  async runFullDemo(): Promise<void> {
    console.log('🎭 CONVERSATIONAL COMBAT SYSTEM DEMO 🎭');
    console.log('=====================================\n');

    await this.demonstrateBasicDialogueProcessing();
    await this.demonstrateStrategicMechanics();
    await this.demonstrateNarrativeGeneration();
    await this.demonstrateTacticalCoordination();
    await this.demonstrateSpectatorMode();
    await this.demonstrateCombatConclusion();

    console.log('\n✨ Demo completed! The Conversational Combat System has showcased:');
    console.log('   • Natural language combat action recognition');
    console.log('   • Strategic dialogue mechanics with D&D 5e integration');
    console.log('   • Dynamic narrative generation');
    console.log('   • Real-time tactical coordination');
    console.log('   • Spectator-friendly combat storytelling');
    console.log('   • AI-powered dialogue enhancement');
  }

  private async demonstrateBasicDialogueProcessing(): Promise<void> {
    console.log('📖 DEMO 1: Basic Dialogue Processing');
    console.log('-------------------------------------');

    // Fighter's intimidation
    console.log('\n🗡️  Fighter Kaelen speaks:');
    const fighterResult = await this.system.processDialogue(
      'fighter_001',
      'By my honor, I will strike you down, foul beast! Face the steel of justice!'
    );

    console.log(`📝 Original: "${fighterResult.originalDialogue.text}"`);
    console.log(`✨ Enhanced: "${fighterResult.enhancedDialogue.text}"`);
    console.log(`🎯 Intent: ${fighterResult.originalDialogue.intent?.type} (Confidence: ${(fighterResult.originalDialogue.intent?.confidence || 0).toFixed(2)})`);
    console.log(`⚡ Mechanics: ${fighterResult.mechanics.bonuses.length} bonuses, ${fighterResult.mechanics.conditions.length} conditions`);

    console.log('\n📜 Generated Narrative:');
    fighterResult.narrative.forEach(n => {
      console.log(`   ${n.type}: ${n.content}`);
    });

    console.log('\n');
  }

  private async demonstrateStrategicMechanics(): Promise<void> {
    console.log('⚔️  DEMO 2: Strategic Dialogue Mechanics');
    console.log('-----------------------------------------');

    // Wizard's tactical spellcasting
    console.log('\n🔮 Wizard Lyra speaks:');
    const wizardResult = await this.system.processDialogue(
      'wizard_001',
      'The arcane laws dictate your destruction! Behold the power of the weave as I call forth fire from the ether!'
    );

    console.log(`📝 Dialogue: "${wizardResult.enhancedDialogue.text}"`);
    console.log(`🎯 Strategic Value: ${(wizardResult.originalDialogue.intent?.strategicValue || 0).toFixed(2)}`);
    console.log(`💫 Mechanical Effects:`);

    wizardResult.mechanics.bonuses.forEach(bonus => {
      console.log(`   • ${bonus.type}: +${bonus.value} to ${bonus.appliesTo.join(', ')} (${bonus.duration} rounds)`);
    });

    if (wizardResult.mechanics.combatAction.save) {
      const save = wizardResult.mechanics.combatAction.save;
      console.log(`   • Forces ${save.ability} save DC ${save.dc}`);
    }

    console.log('\n');
  }

  private async demonstrateNarrativeGeneration(): Promise<void> {
    console.log('📚 DEMO 3: Dynamic Narrative Generation');
    console.log('---------------------------------------');

    // Rogue's witty deception
    console.log('\n🗡️  Rogue Shadow speaks:');
    const rogueResult = await this.system.processDialogue(
      'rogue_001',
      'Hey dragon, is that your treasure? I think I saw some goblins running off with your favorite gold piece! Too easy!'
    );

    console.log(`📝 Dialogue: "${rogueResult.enhancedDialogue.text}"`);
    console.log(`🎭 Emotional Tone Analysis:`);

    if (rogueResult.originalDialogue.intent?.emotionalTone) {
      const emotions = rogueResult.originalDialogue.intent.emotionalTone;
      Object.entries(emotions).forEach(([emotion, value]) => {
        if (value > 0.3) {
          console.log(`   • ${emotion}: ${(value * 100).toFixed(1)}%`);
        }
      });
    }

    console.log('\n🎬 Cinematic Elements:');
    const cinematicNarrative = rogueResult.narrative.filter(n => n.cinematic);
    cinematicNarrative.forEach(n => {
      console.log(`   ⭐ ${n.content}`);
    });

    console.log('\n');
  }

  private async demonstrateTacticalCoordination(): Promise<void> {
    console.log('🎯 DEMO 4: Tactical Coordination');
    console.log('-------------------------------');

    // Start a coordinated conversation
    const conversation = this.system.startConversation(
      ['fighter_001', 'wizard_001', 'rogue_001'],
      'dragon_encounter_coordination'
    );

    console.log('🤝 Team coordination initiated!');

    // Get tactical suggestions
    console.log('\n💡 Tactical Suggestions for Kaelen:');
    const fighterSuggestions = await this.system.getTacticalSuggestions('fighter_001', 'dragon_encounter');
    fighterSuggestions.slice(0, 3).forEach((suggestion, index) => {
      console.log(`   ${index + 1}. ${suggestion.text} (Priority: ${suggestion.priority})`);
      console.log(`      Expected: ${suggestion.expectedOutcome}`);
    });

    // Process coordinated dialogue
    console.log('\n📢 Coordinated Dialogue:');
    const coordinationResult = await this.system.processDialogue(
      'wizard_001',
      'Team, on my mark! Kaelen, engage from the left flank while Shadow positions for backstab. I\'ll prepare fire support when the dragon exposes its underbelly!'
    );

    console.log(`🎯 Coordination Type: ${coordinationResult.originalDialogue.intent?.type}`);
    console.log(`🔗 Synergies Identified: ${coordinationResult.mechanics.synergies.join(', ')}`);

    console.log('\n');
  }

  private async demonstrateSpectatorMode(): Promise<void> {
    console.log('👁️  DEMO 5: Spectator-Friendly Narrative');
    console.log('----------------------------------------');

    // Generate comprehensive spectator narrative
    console.log('📺 Generating combat broadcast...\n');

    const spectatorNarrative = this.system.generateSpectatorNarrative('entire_combat');

    console.log('📡 Combat Summary:');
    console.log(`   ${spectatorNarrative.summary}\n`);

    console.log('🔥 Key Cinematic Moments:');
    spectatorNarrative.keyMoments.slice(0, 3).forEach((moment, index) => {
      console.log(`   ${index + 1}. ${moment}`);
    });

    console.log('\n💬 Dialogue Highlights:');
    spectatorNarrative.dialogueHighlights.slice(0, 3).forEach((quote, index) => {
      console.log(`   ${index + 1}. "${quote}"`);
    });

    console.log('\n📈 Tactical Analysis:');
    console.log(`   ${spectatorNarrative.tacticalAnalysis}`);

    console.log('\n');
  }

  private async demonstrateCombatConclusion(): Promise<void> {
    console.log('🏁 DEMO 6: Combat Resolution');
    console.log('---------------------------');

    // Dragon's response
    console.log('\n🐉 Inferno the Dragon roars:');
    const dragonResult = await this.system.processDialogue(
      'dragon_001',
      'FOOLISH MORTALS! YOU DARE CHALLENGE INFERNO IN MY OWN LAIR? YOUR BONES WILL JOIN THE OTHERS IN MY TREASURE PILES! BURN, BURN TO ASHES!'
    );

    console.log(`🔥 Dragon\'s fury: ${dragonResult.enhancedDialogue.text}`);
    console.log(`💢 Emotional Intensity: High (Anger: ${(dragonResult.originalDialogue.intent?.emotionalTone.anger || 0).toFixed(2)})`);

    // Final state report
    const combatState = this.system.getCombatState();
    console.log('\n📊 Combat State Report:');
    console.log(`   • Total Events: ${combatState.eventSummary.totalEvents}`);
    console.log(`   • Dialogue Events: ${combatState.eventSummary.dialogueEvents}`);
    console.log(`   • Action Events: ${combatState.eventSummary.actionEvents}`);
    console.log(`   • Combat Intensity: ${(combatState.combatIntensity * 100).toFixed(1)}%`);
    console.log(`   • System Metrics: ${combatState.systemMetrics.dialoguesProcessed} dialogues processed`);

    console.log('\n🎉 Combat continues with enhanced dialogue-driven mechanics!');
  }

  async demonstrateAdvancedFeatures(): Promise<void> {
    console.log('🚀 ADVANCED FEATURES DEMO');
    console.log('==========================');

    // Demonstrate AI enhancement
    console.log('\n🤖 AI Dialogue Enhancement:');
    const originalText = "I will hit the dragon";
    const character = createSampleCharacters()[0]; // Fighter

    const enhancement = await this.system['dialogueEnhancement'].enhanceDialogue(
      originalText,
      character,
      {
        type: 'attack',
        emotionalTone: {
          anger: 0.8,
          confidence: 0.7,
          fear: 0.1,
          humor: 0.2,
          seriousness: 0.9,
          desperation: 0.3
        },
        confidence: 0.9,
        strategicValue: 0.7
      } as any,
      createCombatContext()
    );

    console.log(`   Original: "${enhancement.originalText}"`);
    console.log(`   Enhanced: "${enhancement.enhancedText}"`);
    console.log(`   Quality: ${(enhancement.quality * 100).toFixed(1)}%`);
    console.log(`   Character Match: ${(enhancement.characterMatch * 100).toFixed(1)}%`);

    enhancement.changes.forEach(change => {
      console.log(`   • ${change.type}: "${change.original}" → "${change.modified}" (${change.reason})`);
    });

    // Export combat data
    console.log('\n💾 Combat Data Export:');
    const exportData = this.system.exportCombatData();
    console.log(`   • Events exported: ${exportData.eventHistory.length}`);
    console.log(`   • Characters: ${exportData.combatContext.characters.length}`);
    console.log(`   • Export timestamp: ${exportData.exportTimestamp.toISOString()}`);
    console.log(`   • System version: ${exportData.version}`);

    console.log('\n');
  }
}

// Run the demo
async function runDemo(): Promise<void> {
  try {
    const demo = new ConversationalCombatDemo();
    await demo.runFullDemo();
    await demo.demonstrateAdvancedFeatures();
  } catch (error) {
    console.error('Demo error:', error);
  }
}

// Export for use in other files
export { runDemo, ConversationalCombatDemo, createCombatContext, createSampleCharacters };

// Run demo if this file is executed directly
if (require.main === module) {
  runDemo();
}