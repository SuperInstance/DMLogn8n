/**
 * Basic Usage Examples for Advanced AI Dialogue System
 *
 * This file demonstrates how to use the core components of the dialogue system
 * for D&D campaigns and role-playing games.
 */

const EmotionalIntelligenceEngine = require('../src/core/EmotionalIntelligenceEngine');
const ContextAwareConversationManager = require('../src/core/ContextAwareConversationManager');
const DynamicVoiceSynthesisEngine = require('../src/voice/DynamicVoiceSynthesisEngine');
const MultiLanguageSupportSystem = require('../src/translation/MultiLanguageSupportSystem');
const ConversationAnalyticsEngine = require('../src/analytics/ConversationAnalyticsEngine');

async function basicExample() {
  console.log('🎭 Advanced AI Dialogue System - Basic Usage Example\n');

  // Initialize the core engines
  console.log('🔧 Initializing dialogue engines...');

  const emotionalEngine = new EmotionalIntelligenceEngine({
    emotionDecayRate: 0.01,
    memoryLimit: 100,
    empathyThreshold: 0.6,
    adaptationRate: 0.1
  });

  const conversationManager = new ContextAwareConversationManager({
    maxConversations: 10,
    shortTermMemoryLimit: 50,
    longTermMemoryLimit: 500
  });

  const voiceEngine = new DynamicVoiceSynthesisEngine({
    defaultProvider: 'local', // Use local TTS for this example
    quality: 'medium'
  });

  const translationEngine = new MultiLanguageSupportSystem({
    defaultProvider: 'local',
    enableCulturalNuance: true
  });

  const analyticsEngine = new ConversationAnalyticsEngine({
    enableRealTimeAnalysis: true
  });

  console.log('✅ Engines initialized successfully!\n');

  // Example 1: Emotional Analysis
  console.log('📊 Example 1: Emotional Analysis');
  console.log('─'.repeat(40));

  const playerMessage = "I'm really excited about this quest, but also a bit nervous about the dragon we might face.";
  const speakerId = 'player_001';

  try {
    const emotionResult = await emotionalEngine.analyzeEmotion(playerMessage, speakerId, {
      race: 'human',
      previousMessages: [],
      environment: { location: 'tavern', atmosphere: 'tense' }
    });

    console.log(`📝 Message: "${playerMessage}"`);
    console.log(`👤 Speaker: ${speakerId}`);
    console.log('\n🧠 Emotional Analysis Results:');
    console.log(`   Dominant Emotion: ${Object.entries(emotionResult.emotionalState).sort((a, b) => b[1] - a[1])[0][0]}`);
    console.log(`   Emotional State:`, emotionResult.emotionalState);
    console.log(`   Confidence: ${(emotionResult.confidence * 100).toFixed(1)}%`);
    console.log(`   Sentiment Score: ${emotionResult.sentiment.score.toFixed(2)}`);

    if (emotionResult.empathyResponse) {
      console.log(`   Suggested Response: ${emotionResult.empathyResponse.suggestedResponses[0]}`);
    }

  } catch (error) {
    console.error('❌ Error in emotional analysis:', error.message);
  }

  console.log('\n');

  // Example 2: Context-Aware Conversation
  console.log('💬 Example 2: Context-Aware Conversation');
  console.log('─'.repeat(40));

  const participants = [
    {
      id: 'player_001',
      name: 'Aria Starweaver',
      role: 'player',
      race: 'elf',
      class: 'wizard',
      background: 'Scholar from the arcane academy'
    },
    {
      id: 'npc_001',
      name: 'Borin Stonehand',
      role: 'npc',
      race: 'dwarf',
      class: 'fighter',
      background: 'Veteran warrior and blacksmith'
    }
  ];

  const campaignContext = {
    campaign: {
      id: 'campaign_001',
      name: 'The Dragon\'s Legacy',
      chapter: 'Chapter 1: The Gathering Storm',
      objectives: ['Investigate dragon sightings', 'Find the ancient artifact', 'Stop the corruption']
    },
    environment: {
      location: {
        name: 'The Rusty Flagon Tavern',
        type: 'tavern',
        description: 'A cozy, fire-lit tavern filled with adventurers'
      },
      time: {
        inGame: '21:30',
        season: 'autumn'
      },
      weather: {
        condition: 'rainy',
        temperature: 'cool'
      },
      atmosphere: 'mysterious'
    }
  };

  try {
    // Initiate conversation
    const conversationInitiation = await conversationManager.initiateConversation(participants, campaignContext);

    console.log(`🎬 Conversation Started: ${conversationInitiation.conversationId}`);
    console.log(`📍 Location: ${campaignContext.environment.location.name}`);
    console.log(`👥 Participants: ${participants.map(p => p.name).join(', ')}`);
    console.log(`🎯 Objectives: ${campaignContext.campaign.objectives.join(', ')}`);

    // Process first message
    const playerMessage1 = "Greetings, Borin. I've heard you might have information about the recent dragon sightings in the region.";
    const messageResult1 = await conversationManager.processMessage(
      conversationInitiation.conversationId,
      playerMessage1,
      'player_001',
      { urgency: 'medium', emotionalState: { curiosity: 0.8, respect: 0.7 } }
    );

    console.log(`\n💭 Aria: "${playerMessage1}"`);
    console.log('🎯 Suggested NPC Responses:');
    messageResult1.suggestions.slice(0, 3).forEach((suggestion, index) => {
      console.log(`   ${index + 1}. ${suggestion.text} (${suggestion.type})`);
    });

    // Process NPC response
    const npcResponse = "Ah, a wizard seeking knowledge about dragons. I've fought my share of the beasts in my time. What specifically brings you to my table, young elf?";
    const messageResult2 = await conversationManager.processMessage(
      conversationInitiation.conversationId,
      npcResponse,
      'npc_001',
      { emotionalState: { experience: 0.9, caution: 0.6 } }
    );

    console.log(`\n⚒️  Borin: "${npcResponse}"`);
    console.log('🧠 Emotional Context Updated:');
    console.log(`   Relationship Trust: ${messageResult2.context.relationship['player_001-npc_001']?.trust?.toFixed(2) || '0.50'}`);
    console.log(`   Conversation Topics: ${messageResult2.context.topics?.join(', ') || 'dragon, knowledge'}`);

    // Track analytics
    await analyticsEngine.trackConversation(conversationInitiation.conversationId, {
      ...messageResult2,
      participants,
      messages: [
        { speakerId: 'player_001', content: playerMessage1, timestamp: new Date().toISOString() },
        { speakerId: 'npc_001', content: npcResponse, timestamp: new Date().toISOString() }
      ]
    });

    console.log('\n📊 Conversation analytics tracked successfully!');

  } catch (error) {
    console.error('❌ Error in conversation management:', error.message);
  }

  console.log('\n');

  // Example 3: Voice Synthesis with Emotion
  console.log('🎙️  Example 3: Voice Synthesis with Emotion');
  console.log('─'.repeat(40));

  const dwarfVoiceConfig = {
    race: 'dwarf',
    gender: 'male',
    age: 'old',
    socialClass: 'common',
    accent: 'nordic',
    characteristics: ['gravelly', 'resonant']
  };

  const emotionalTone = {
    anger: 0.3,
    trust: 0.8,
    anticipation: 0.6
  };

  try {
    const dwarvenText = "By my beard! I'll help ye fight this dragon. Stone and steel guide us!";

    console.log(`📝 Text: "${dwarvenText}"`);
    console.log(`🎭 Voice Profile: Dwarf Male, Old, Nordic Accent`);
    console.log(`😊 Emotional Tone: Angry (30%), Trust (80%), Anticipation (60%)`);

    const voiceResult = await voiceEngine.synthesizeSpeech(
      dwarvenText,
      dwarfVoiceConfig,
      emotionalTone,
      { realtime: false }
    );

    console.log(`✅ Voice synthesis completed!`);
    console.log(`   Audio Duration: ${voiceResult.duration}s`);
    console.log(`   Processing Time: ${voiceResult.processingTime}ms`);
    console.log(`   Provider: ${voiceResult.provider}`);
    console.log(`   Audio Size: ${(voiceResult.audioBuffer.length / 1024).toFixed(1)} KB`);

  } catch (error) {
    console.error('❌ Error in voice synthesis:', error.message);
    console.log('💡 Note: For this example, voice synthesis may fail if no TTS provider is configured');
  }

  console.log('\n');

  // Example 4: Multi-Language Support
  console.log('🌍 Example 4: Multi-Language Support');
  console.log('─'.repeat(40));

  try {
    const englishText = "The ancient dragon speaks in Draconic tongue: 'Mortals, you dare to challenge me?'";

    console.log(`🇺🇸 Original (English): "${englishText}"`);

    // Translate to Spanish
    const spanishTranslation = await translationEngine.translateText(
      englishText,
      'es',
      'en',
      {
        preserveDNDTerminology: true,
        fantasyLanguage: 'draconic',
        context: { campaign: 'fantasy', tone: 'epic' }
      }
    );

    console.log(`🇪🇸 Spanish: "${spanishTranslation}"`);

    // Translate to Japanese
    const japaneseTranslation = await translationEngine.translateText(
      englishText,
      'ja',
      'en',
      {
        preserveDNDTerminology: true,
        fantasyLanguage: 'draconic',
        context: { campaign: 'fantasy', tone: 'epic' }
      }
    );

    console.log(`🇯🇵 Japanese: "${japaneseTranslation}"`);

    // Demonstrate fantasy language handling
    const draconicPhrase = "Vercath thak zhaan!"; // "Mortal power awaits!"
    const draconicTranslation = await translationEngine.translateText(
      draconicPhrase,
      'en',
      'draconic',
      { fantasyLanguage: 'draconic' }
    );

    console.log(`🐉 Draconic: "${draconicPhrase}"`);
    console.log(`🇺🇸 English Translation: "${draconicTranslation}"`);

  } catch (error) {
    console.error('❌ Error in translation:', error.message);
    console.log('💡 Note: Translation may fail if no translation provider is configured');
  }

  console.log('\n');

  // Example 5: Analytics and Insights
  console.log('📈 Example 5: Analytics and Insights');
  console.log('─'.repeat(40));

  try {
    // Generate conversation analytics report
    const analyticsReport = analyticsEngine.generateAnalyticsReport({
      period: 'session',
      conversationIds: [conversationInitiation?.conversationId].filter(Boolean)
    });

    console.log('📊 Analytics Report Summary:');
    console.log(`   Total Conversations: ${analyticsReport.summary.totalConversations}`);
    console.log(`   Average Quality: ${(analyticsReport.summary.overallQuality * 100).toFixed(1)}%`);
    console.log(`   Total Messages: ${analyticsReport.summary.totalMessages}`);
    console.log(`   Average Duration: ${analyticsReport.summary.averageDuration}s`);
    console.log(`   Overall Sentiment: ${analyticsReport.summary.overallSentiment.toFixed(2)}`);

    console.log('\n🎯 Recommendations:');
    analyticsReport.recommendations.forEach((rec, index) => {
      console.log(`   ${index + 1}. ${rec.title} (${rec.priority} priority)`);
      console.log(`      ${rec.description}`);
      if (rec.actionItems && rec.actionItems.length > 0) {
        console.log(`      Actions: ${rec.actionItems.join(', ')}`);
      }
    });

  } catch (error) {
    console.error('❌ Error generating analytics:', error.message);
  }

  console.log('\n');

  // Example 6: Personality Adaptation
  console.log('🧠 Example 6: Personality Adaptation');
  console.log('─'.repeat(40));

  try {
    console.log('📊 Initial NPC Personality Profile:');
    const initialProfile = emotionalEngine.getPersonalityProfile();
    Object.entries(initialProfile).forEach(([trait, data]) => {
      console.log(`   ${trait}: ${data.current.toFixed(2)} (min: ${data.min}, max: ${data.max})`);
    });

    // Simulate several positive interactions
    const positiveInteractions = [
      "Thank you for your wisdom, Borin. Your advice has been invaluable.",
      "I really appreciate you sharing your dragon-hunting experience with us.",
      "Your blacksmithing skills are amazing! That sword you crafted is perfect.",
      "It's an honor to adventure with someone as experienced as you."
    ];

    console.log('\n💬 Processing positive interactions...');
    for (const message of positiveInteractions) {
      await emotionalEngine.analyzeEmotion(message, 'npc_001', {
        speakerRole: 'player',
        relationshipType: 'friendly'
      });
    }

    console.log('📊 Updated NPC Personality Profile:');
    const updatedProfile = emotionalEngine.getPersonalityProfile();
    Object.entries(updatedProfile).forEach(([trait, data]) => {
      const change = data.current - initialProfile[trait].current;
      const arrow = change > 0 ? '↑' : change < 0 ? '↓' : '→';
      console.log(`   ${trait}: ${data.current.toFixed(2)} ${arrow} (${change > 0 ? '+' : ''}${change.toFixed(3)})`);
    });

  } catch (error) {
    console.error('❌ Error in personality adaptation:', error.message);
  }

  console.log('\n');

  // Cleanup
  console.log('🧹 Cleaning up resources...');
  emotionalEngine.reset();
  conversationManager.reset();
  analyticsEngine.reset();

  console.log('✅ Basic usage examples completed successfully!');
  console.log('\n🎉 The Advanced AI Dialogue System is ready for your D&D campaigns!');
  console.log('\n📚 For more examples and documentation, see:');
  console.log('   • docs/README.md - Complete documentation');
  console.log('   • examples/ - Additional usage examples');
  console.log('   • tests/ - Integration tests');
}

// Character development example
async function characterDevelopmentExample() {
  console.log('\n🎭 Character Development Example');
  console.log('─'.repeat(40));

  const emotionalEngine = new EmotionalIntelligenceEngine();
  const conversationManager = new ContextAwareConversationManager();

  // Create a complex character arc
  const character = {
    id: 'character_arthur',
    name: 'Arthur Blackwood',
    role: 'player',
    race: 'human',
    class: 'paladin',
    background: 'Former knight seeking redemption'
  };

  // Personality development over time
  console.log('📈 Character: Arthur Blackwood - Redemption Arc');

  const personalityProgression = [
    {
      scene: 'Introduction - Haunted and Guilty',
      traits: { neuroticism: 0.8, agreeableness: 0.3, extraversion: 0.2 },
      message: "I don't deserve to be called a paladin anymore... after what happened at the monastery."
    },
    {
      scene: 'First Act of Kindness - Reluctant Hero',
      traits: { neuroticism: 0.6, agreeableness: 0.5, extraversion: 0.3 },
      message: "Fine. I'll help you rescue the villagers, but don't expect me to be a hero."
    },
    {
      scene: 'Moral Choice - Finding Purpose',
      traits: { neuroticism: 0.4, agreeableness: 0.7, extraversion: 0.5 },
      message: "You're right. My past doesn't define me. It's what I do now that matters."
    },
    {
      scene: 'Redemption - True Paladin',
      traits: { neuroticism: 0.2, agreeableness: 0.9, extraversion: 0.7 },
      message: "I will protect the innocent, no matter the cost. This is my oath, my purpose."
    }
  ];

  for (let i = 0; i < personalityProgression.length; i++) {
    const stage = personalityProgression[i];

    console.log(`\n📍 ${stage.scene}`);
    console.log(`💬 "${stage.message}"`);

    // Update personality
    Object.entries(stage.traits).forEach(([trait, value]) => {
      emotionalEngine.setPersonalityTrait(trait, value);
    });

    // Analyze the emotional impact
    const analysis = await emotionalEngine.analyzeEmotion(
      stage.message,
      character.id,
      { characterDevelopment: true, sceneNumber: i + 1 }
    );

    console.log(`🧠 Emotional State: ${Object.entries(analysis.emotionalState)
      .sort((a, b) => b[1] - a[1])[0][0]} (${Object.entries(analysis.emotionalState)
      .sort((a, b) => b[1] - a[1])[0][1].toFixed(2)})`);

    // Show personality profile
    const profile = emotionalEngine.getPersonalityProfile();
    console.log(`🎭 Personality: ${Object.entries(profile)
      .map(([trait, data]) => `${trait}: ${data.current.toFixed(2)}`)
      .join(', ')}`);
  }

  console.log('\n✨ Character development arc completed!');
}

// Run examples
if (require.main === module) {
  basicExample()
    .then(() => characterDevelopmentExample())
    .then(() => {
      console.log('\n🎯 All examples completed successfully!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Error running examples:', error);
      process.exit(1);
    });
}

module.exports = {
  basicExample,
  characterDevelopmentExample
};