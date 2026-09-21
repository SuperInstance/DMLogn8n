const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const { Configuration, OpenAIApi } = require('openai');

// Initialize OpenAI
const configuration = new Configuration({
  apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

// Generate story hook
router.post('/story-hook', auth, async (req, res) => {
  try {
    const { campaignName, tone, playerCount, averageLevel, existingElements } = req.body;

    const prompt = `Generate a compelling D&D story hook for a campaign called "${campaignName}".

Campaign Details:
- Tone: ${tone || 'balanced'}
- Party: ${playerCount || 4} players, average level ${averageLevel || 3}
- Existing Elements: ${existingElements || 'None specified'}

Please provide:
1. A compelling hook title
2. Brief setup (2-3 sentences)
3. Key NPCs involved
4. Primary location
5. Potential complications
6. Possible rewards

Make it engaging and suitable for the specified tone and party level.`;

    const response = await openai.createCompletion({
      model: process.env.OPENAI_MODEL || 'text-davinci-003',
      prompt,
      max_tokens: 800,
      temperature: 0.8,
      top_p: 1,
      frequency_penalty: 0.1,
      presence_penalty: 0.1,
    });

    res.json({
      success: true,
      data: {
        hook: response.data.choices[0].text.trim(),
        usage: response.data.usage
      }
    });
  } catch (error) {
    console.error('AI story hook error:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to generate story hook' }
    });
  }
});

// Generate character backstory
router.post('/character-backstory', auth, async (req, res) => {
  try {
    const { characterName, race, class: characterClass, level, personality, campaign } = req.body;

    const prompt = `Generate a detailed backstory for a D&D character.

Character Details:
- Name: ${characterName}
- Race: ${race}
- Class: ${characterClass}
- Level: ${level}
- Personality: ${personality || 'Not specified'}
- Campaign: ${campaign || 'Not specified'}

Please create a backstory that:
1. Explains their motivation for adventuring
2. Includes significant life events
3. Establishes relationships and connections
4. Provides plot hooks for the DM
5. Fits naturally with their race and class
6. Is approximately 300-500 words

Make it compelling and provide depth for roleplaying.`;

    const response = await openai.createCompletion({
      model: process.env.OPENAI_MODEL || 'text-davinci-003',
      prompt,
      max_tokens: 600,
      temperature: 0.7,
      top_p: 1,
      frequency_penalty: 0.2,
      presence_penalty: 0.2,
    });

    res.json({
      success: true,
      data: {
        backstory: response.data.choices[0].text.trim(),
        usage: response.data.usage
      }
    });
  } catch (error) {
    console.error('AI backstory error:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to generate character backstory' }
    });
  }
});

// Generate NPC dialogue
router.post('/npc-dialogue', auth, async (req, res) => {
  try {
    const { npcName, role, personality, situation, playerAction, tone } = req.body;

    const prompt = `Generate dialogue for an NPC in a D&D campaign.

NPC Details:
- Name: ${npcName}
- Role: ${role}
- Personality: ${personality}
- Situation: ${situation}
- Player Action: ${playerAction || 'Players are approaching'}
- Campaign Tone: ${tone || 'balanced'}

Generate dialogue that:
1. Reflects the NPC's personality and role
2. Responds naturally to the situation
3. Provides information or advancement
4. Offers roleplaying opportunities
5. Includes emotional context and descriptions
6. Is approximately 200-400 words

Make it engaging and authentic to the character.`;

    const response = await openai.createCompletion({
      model: process.env.OPENAI_MODEL || 'text-davinci-003',
      prompt,
      max_tokens: 500,
      temperature: 0.8,
      top_p: 1,
      frequency_penalty: 0.3,
      presence_penalty: 0.3,
    });

    res.json({
      success: true,
      data: {
        dialogue: response.data.choices[0].text.trim(),
        usage: response.data.usage
      }
    });
  } catch (error) {
    console.error('AI dialogue error:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to generate NPC dialogue' }
    });
  }
});

// Balance encounter
router.post('/balance-encounter', auth, async (req, res) => {
  try {
    const { partyLevel, partySize, difficulty, terrain, existingMonsters } = req.body;

    const prompt = `Create a balanced D&D 5e combat encounter.

Party Details:
- Level: ${partyLevel}
- Size: ${partySize} players
- Desired Difficulty: ${difficulty}
- Terrain: ${terrain || 'Open battlefield'}
- Existing Monsters: ${existingMonsters || 'None'}

Design an encounter that:
1. Is appropriately challenging for the specified difficulty
2. Uses creatures with appropriate CR for the party level
3. Takes terrain into account for tactics and advantages
4. Includes interesting combat mechanics and tactics
5. Provides suggestions for monster actions and strategies
6. Lists recommended treasure and rewards

Please provide:
- Monster composition (names and quantities)
- Total encounter XP
- Recommended tactics
- Environmental factors
- Treasure suggestions

Make it tactical and engaging.`;

    const response = await openai.createCompletion({
      model: process.env.OPENAI_MODEL || 'text-davinci-003',
      prompt,
      max_tokens: 700,
      temperature: 0.6,
      top_p: 1,
      frequency_penalty: 0.1,
      presence_penalty: 0.1,
    });

    res.json({
      success: true,
      data: {
        encounter: response.data.choices[0].text.trim(),
        usage: response.data.usage
      }
    });
  } catch (error) {
    console.error('AI encounter error:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to generate encounter' }
    });
  }
});

// Generate location description
router.post('/location-description', auth, async (req, res) => {
  try {
    const { locationName, type, atmosphere, purpose, history, secrets } = req.body;

    const prompt = `Generate a detailed D&D location description.

Location Details:
- Name: ${locationName}
- Type: ${type}
- Atmosphere: ${atmosphere || 'Mysterious'}
- Purpose: ${purpose || 'Exploration'}
- History: ${history || 'Unknown'}
- Secrets: ${secrets || 'Hidden mysteries'}

Create a description that:
1. Provides vivid sensory details (sights, sounds, smells)
2. Establishes mood and atmosphere
3. Includes interactive elements and points of interest
4. Suggests potential dangers or opportunities
5. Hints at the location's history and secrets
6. Is approximately 300-500 words

Make it immersive and engaging for exploration.`;

    const response = await openai.createCompletion({
      model: process.env.OPENAI_MODEL || 'text-davinci-003',
      prompt,
      max_tokens: 600,
      temperature: 0.7,
      top_p: 1,
      frequency_penalty: 0.2,
      presence_penalty: 0.2,
    });

    res.json({
      success: true,
      data: {
        description: response.data.choices[0].text.trim(),
        usage: response.data.usage
      }
    });
  } catch (error) {
    console.error('AI location error:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to generate location description' }
    });
  }
});

// Generate quest
router.post('/generate-quest', auth, async (req, res) => {
  try {
    const { questTitle, questType, difficulty, location, questGiver, rewards, partyLevel } = req.body;

    const prompt = `Generate a detailed D&D quest.

Quest Details:
- Title: ${questTitle}
- Type: ${questType}
- Difficulty: ${difficulty}
- Location: ${location}
- Quest Giver: ${questGiver}
- Rewards: ${rewards || 'Gold and experience'}
- Party Level: ${partyLevel}

Create a quest that includes:
1. Detailed objectives (3-5 clear goals)
2. Interesting NPCs involved
3. Potential complications and obstacles
4. Choices and consequences for players
5. Climax and resolution options
6. Bonus objectives or side opportunities

Make it engaging with meaningful choices and outcomes appropriate for the party level.`;

    const response = await openai.createCompletion({
      model: process.env.OPENAI_MODEL || 'text-davinci-003',
      prompt,
      max_tokens: 800,
      temperature: 0.7,
      top_p: 1,
      frequency_penalty: 0.1,
      presence_penalty: 0.1,
    });

    res.json({
      success: true,
      data: {
        quest: response.data.choices[0].text.trim(),
        usage: response.data.usage
      }
    });
  } catch (error) {
    console.error('AI quest error:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to generate quest' }
    });
  }
});

// General creative assistance
router.post('/creative-assist', auth, async (req, res) => {
  try {
    const { prompt, context, tone, length } = req.body;

    const enhancedPrompt = `You are a creative assistant for a Dungeon Master running a D&D campaign.

Context: ${context || 'Generic D&D campaign'}
Tone: ${tone || 'balanced'}
Desired Length: ${length || 'medium'}

User Request: ${prompt}

Please provide a helpful, creative response that assists with D&D campaign management, storytelling, or problem-solving. Be specific, practical, and inspiring.`;

    const response = await openai.createCompletion({
      model: process.env.OPENAI_MODEL || 'text-davinci-003',
      prompt: enhancedPrompt,
      max_tokens: length === 'short' ? 300 : length === 'long' ? 1000 : 600,
      temperature: 0.7,
      top_p: 1,
      frequency_penalty: 0.2,
      presence_penalty: 0.2,
    });

    res.json({
      success: true,
      data: {
        response: response.data.choices[0].text.trim(),
        usage: response.data.usage
      }
    });
  } catch (error) {
    console.error('AI creative assist error:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to generate creative assistance' }
    });
  }
});

module.exports = router;