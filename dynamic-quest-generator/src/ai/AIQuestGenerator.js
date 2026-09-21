import OpenAI from 'openai'
import { QUEST_CONFIG } from '../../config/quest-config.js'

export class AIQuestGenerator {
  constructor() {
    this.openai = new OpenAI({
      apiKey: process.env.OPENAI_API_KEY
    })

    this.systemPrompt = `You are a master dungeon master and quest designer for a fantasy RPG. Your task is to create engaging, personalized quests that adapt to player preferences and skill levels.

Guidelines:
- Create immersive storylines with clear objectives
- Ensure quests are appropriate for the specified difficulty level (1-7)
- Include meaningful choices and consequences
- Generate balanced rewards based on difficulty and effort
- Consider player class, level, and preferences in quest design
- Create diverse objectives beyond just combat (exploration, social, mystery, crafting)
- Ensure all generated content is appropriate for a general audience

Always respond with valid JSON that can be parsed.`

    this.questTemplates = {
      hero_journey: "A classic adventure where the player must rise to meet a great challenge and grow in the process.",
      mystery_investigation: "An intriguing puzzle that requires careful investigation and deduction to solve.",
      rescue_mission: "A time-sensitive quest to save someone important from danger.",
      exploration_discovery: "An adventure into uncharted territories to uncover ancient secrets.",
      political_intrigue: "A complex web of alliances, betrayals, and diplomatic challenges.",
      personal_redemption: "A deeply personal quest to atone for past mistakes or help someone else find redemption.",
      revenge_justice: "A quest to bring wrongdoers to justice or seek vengeance for past harms.",
      protection_defense: "A defensive mission to protect people, places, or ideals from threats."
    }
  }

  /**
   * Generate a quest using AI
   */
  async generateQuest(params) {
    try {
      const { player, context, type, category, difficulty, guildContext, partySize } = params

      // Build the quest prompt
      const prompt = this.buildQuestPrompt(params)

      // Generate quest content
      const response = await this.openai.chat.completions.create({
        model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: this.systemPrompt },
          { role: 'user', content: prompt }
        ],
        temperature: parseFloat(process.env.AI_TEMPERATURE) || 0.7,
        max_tokens: parseInt(process.env.AI_MAX_TOKENS) || 4000,
        top_p: parseFloat(process.env.AI_TOP_P) || 0.9,
        frequency_penalty: parseFloat(process.env.AI_FREQUENCY_PENALTY) || 0.5,
        presence_penalty: parseFloat(process.env.AI_PRESENCE_PENALTY) || 0.3
      })

      const content = response.choices[0].message.content

      // Parse the AI response
      const questData = this.parseAIResponse(content)

      // Enhance with structured data
      const enhancedQuest = this.enhanceQuestData(questData, params)

      return enhancedQuest

    } catch (error) {
      console.error('Error generating AI quest:', error)
      throw new Error(`AI quest generation failed: ${error.message}`)
    }
  }

  /**
   * Build quest prompt for AI
   */
  buildQuestPrompt(params) {
    const { player, context, type, category, difficulty, guildContext, partySize } = params

    let prompt = `Generate a ${type} quest in the ${category} category with difficulty ${difficulty}/7.\n\n`

    // Add player context
    if (player) {
      prompt += `Player Context:\n`
      prompt += `- Level: ${player.stats.level}\n`
      prompt += `- Class: ${player.character.class}\n`
      prompt += `- Race: ${player.character.race}\n`
      prompt += `- Background: ${player.character.background}\n`
      prompt += `- Alignment: ${player.character.alignment}\n`
      prompt += `- Completion Rate: ${context.completionRate || 'Unknown'}\n`
      prompt += `- Recent Performance: ${context.recentPerformance || 'Unknown'}\n`
    }

    // Add preferences
    if (context.preferences) {
      prompt += `\nPlayer Preferences:\n`
      prompt += `- Combat: ${(context.preferences.combat || 0.5) * 100}%\n`
      prompt += `- Exploration: ${(context.preferences.exploration || 0.5) * 100}%\n`
      prompt += `- Social: ${(context.preferences.social || 0.5) * 100}%\n`
      prompt += `- Mystery: ${(context.preferences.mystery || 0.5) * 100}%\n`
      prompt += `- Crafting: ${(context.preferences.crafting || 0.5) * 100}%\n`
    }

    // Add party context
    if (partySize && partySize > 1) {
      prompt += `\nParty Context:\n`
      prompt += `- Party Size: ${partySize}\n`
      if (context.partyComposition) {
        prompt += `- Party Composition: ${context.partyComposition.join(', ')}\n`
      }
    }

    // Add guild context
    if (guildContext) {
      prompt += `\nGuild Context:\n`
      prompt += `- Guild Size: ${guildContext.memberCount}\n`
      prompt += `- Average Level: ${guildContext.averageLevel}\n`
      prompt += `- Available Roles: ${JSON.stringify(guildContext.availableRoles)}\n`
    }

    // Add recent quest history
    if (context.recentQuestTypes && context.recentQuestTypes.length > 0) {
      prompt += `\nRecent Quest Types (avoid repeating these too soon):\n`
      prompt += `- ${context.recentQuestTypes.join(', ')}\n`
    }

    // Add world state
    if (context.worldState) {
      prompt += `\nWorld State: ${context.worldState}\n`
    }

    // Add quest requirements
    prompt += `\nQuest Requirements:\n`
    prompt += `- Generate 2-5 meaningful objectives\n`
    prompt += `- Include at least one non-combat objective if appropriate\n`
    prompt += `- Provide clear success conditions\n`
    prompt += `- Suggest appropriate rewards based on difficulty\n`
    prompt += `- Create engaging story elements\n`

    // Add difficulty-specific instructions
    prompt += this.getDifficultyInstructions(difficulty)

    // Add category-specific instructions
    prompt += this.getCategoryInstructions(category)

    // Add template selection
    const template = this.selectQuestTemplate(context, difficulty)
    prompt += `\nStory Template: ${template.name}\n`
    prompt += `Template Description: ${template.description}\n`

    // Add structure requirements
    prompt += `\nRequired JSON Structure:\n`
    prompt += `{
  "title": "Quest title",
  "description": "Detailed quest description (2-4 paragraphs)",
  "objectives": [
    {
      "title": "Objective title",
      "description": "What the player needs to do",
      "type": "kill/collect/explore/talk_to/craft/social_interaction",
      "target": "What they need to target",
      "required": number,
      "optional": boolean,
      "hidden": boolean,
      "location": "Where this takes place"
    }
  ],
  "story": {
    "introduction": "How the quest begins",
    "background": "Important context",
    "climax": "The main challenge",
    "resolution": "How it concludes",
    "epilogue": "What happens after"
  },
  "rewards": [
    {
      "type": "experience/gold/reputation/item/equipment",
      "amount": number,
      "description": "Reward description"
    }
  ],
  "npcs": [
    {
      "name": "NPC name",
      "role": "quest_giver/ally/enemy/neutral",
      "description": "Brief description",
      "dialogue": ["Sample dialogue lines"]
    }
  ],
  "locations": [
    {
      "name": "Location name",
      "description": "What it's like",
      "importance": "Why it matters"
    }
  ],
  "choices": [
    {
      "description": "Choice description",
      "consequences": "What happens if this choice is made"
    }
  ],
  "difficulty": ${difficulty},
  "estimatedTime": "Estimated completion time in minutes",
  "tags": ["relevant", "tags"]
}`

    return prompt
  }

  /**
   * Get difficulty-specific instructions
   */
  getDifficultyInstructions(difficulty) {
    const instructions = {
      1: "\nDifficulty 1 (Trivial): Very simple quest for new players. Minimal danger, clear guidance, generous rewards.",
      2: "\nDifficulty 2 (Easy): Straightforward quest with minor challenges. Good for learning game mechanics.",
      3: "\nDifficulty 3 (Normal): Standard quest with balanced challenges. Requires basic strategy and game knowledge.",
      4: "\nDifficulty 4 (Hard): Challenging quest that requires good preparation and strategy. Higher stakes.",
      5: "\nDifficulty 5 (Expert): Difficult quest requiring advanced tactics and optimal character builds. Significant consequences.",
      6: "\nDifficulty 6 (Legendary): Very difficult quest for experienced players. Multiple phases, tough enemies, complex mechanics.",
      7: "\nDifficulty 7 (Mythic): Extremely challenging quest requiring mastery of game systems. Epic scale, permanent consequences."
    }

    return instructions[difficulty] || instructions[3]
  }

  /**
   * Get category-specific instructions
   */
  getCategoryInstructions(category) {
    const instructions = {
      combat: "\nCombat Quest: Focus on battles, tactics, enemy variety. Include different types of combat encounters.",
      exploration: "\nExploration Quest: Emphasize discovery, mapping, environmental challenges. Make the journey itself rewarding.",
      social: "\nSocial Quest: Center on interactions, dialogue, relationships. Include persuasion, negotiation, and social consequences.",
      mystery: "\nMystery Quest: Create intrigue, clues, deduction. Players should piece together information to solve puzzles.",
      crafting: "\nCrafting Quest: Focus on gathering materials, creating items, quality requirements. Include crafting challenges.",
      collection: "\nCollection Quest: Emphasize gathering, hunting for rare items. Make collection interesting and varied.",
      escort: "\nEscort Quest: Protect NPCs, manage risks, time sensitivity. Create tension and protection challenges.",
      delivery: "\nDelivery Quest: Time-sensitive transportation, route challenges. Include obstacles and urgency.",
      dungeon: "\nDungeon Quest: Multi-area exploration, variety of challenges, environmental puzzles. Create dungeon atmosphere.",
      boss_battle: "\nBoss Battle Quest: Build up to major confrontation, phases, tactics. Create epic final confrontation."
    }

    return instructions[category] || ""
  }

  /**
   * Select appropriate quest template
   */
  selectQuestTemplate(context, difficulty) {
    const templates = Object.entries(this.questTemplates)

    // Filter templates based on player preferences
    if (context.preferences) {
      const maxPref = Math.max(...Object.values(context.preferences))
      if (maxPref > 0.7) {
        // Prefer templates that match high preferences
        const prefType = Object.entries(context.preferences).find(([, value]) => value === maxPref)[0]
        if (prefType === 'social') {
          return { name: 'political_intrigue', description: this.questTemplates.political_intrigue }
        } else if (prefType === 'mystery') {
          return { name: 'mystery_investigation', description: this.questTemplates.mystery_investigation }
        }
      }
    }

    // Consider recent quest types
    if (context.recentQuestTypes && context.recentQuestTypes.length > 0) {
      const avoidTypes = context.recentQuestTypes.slice(-3)
      const availableTemplates = templates.filter(([name]) => !avoidTypes.includes(name))
      if (availableTemplates.length > 0) {
        const selected = availableTemplates[Math.floor(Math.random() * availableTemplates.length)]
        return { name: selected[0], description: selected[1] }
      }
    }

    // Consider difficulty
    if (difficulty >= 6) {
      return { name: 'hero_journey', description: this.questTemplates.hero_journey }
    } else if (difficulty <= 2) {
      return { name: 'rescue_mission', description: this.questTemplates.rescue_mission }
    }

    // Default random selection
    const selected = templates[Math.floor(Math.random() * templates.length)]
    return { name: selected[0], description: selected[1] }
  }

  /**
   * Parse AI response
   */
  parseAIResponse(content) {
    try {
      // Try to extract JSON from the response
      const jsonMatch = content.match(/\{[\s\S]*\}/)
      if (!jsonMatch) {
        throw new Error('No JSON found in AI response')
      }

      const parsed = JSON.parse(jsonMatch[0])
      return parsed

    } catch (error) {
      console.error('Error parsing AI response:', error)
      console.error('Raw content:', content)

      // Return fallback structure
      return this.getFallbackQuest()
    }
  }

  /**
   * Enhance quest data with additional structure
   */
  enhanceQuestData(questData, params) {
    const { difficulty, type, category, player } = params

    // Ensure required fields exist
    const enhanced = {
      ...questData,
      type: questData.type || type,
      category: questData.category || category,
      difficulty: questData.difficulty || difficulty,
      levelRequirement: this.calculateLevelRequirement(questData, params),
      estimatedTime: questData.estimatedTime || this.estimateQuestTime(questData, difficulty),

      // Structure objectives
      objectives: this.structureObjectives(questData.objectives || []),

      // Structure rewards
      rewards: this.structureRewards(questData.rewards || [], difficulty),

      // Add metadata
      tags: [...new Set([...(questData.tags || []), type, category])],
      aiGenerated: true,
      aiModel: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
      aiConfidence: this.calculateConfidence(questData),

      // Add branching support
      branching: {
        enabled: questData.choices && questData.choices.length > 0,
        availablePaths: questData.choices || [],
        currentPath: null,
        completedPaths: [],
        pathHistory: []
      }
    }

    // Add player-specific adaptations
    if (player) {
      enhanced.personalized = true
      enhanced.personalizationData = {
        playerLevel: player.stats.level,
        playerClass: player.character.class,
        adaptations: this.calculateAdaptations(player, questData)
      }
    }

    // Add world impact
    enhanced.worldImpact = this.generateWorldImpact(questData, difficulty)

    return enhanced
  }

  /**
   * Structure objectives properly
   */
  structureObjectives(objectives) {
    return objectives.map((obj, index) => ({
      id: obj.id || `obj_${index + 1}`,
      title: obj.title || `Objective ${index + 1}`,
      description: obj.description || '',
      type: this.normalizeObjectiveType(obj.type),
      target: obj.target || 'unknown',
      current: 0,
      required: obj.required || 1,
      completed: false,
      optional: obj.optional || false,
      hidden: obj.hidden || false,
      location: obj.location || null,
      requirements: obj.requirements || [],
      rewards: obj.rewards || [],
      choices: obj.choices || [],
      branches: obj.branches || []
    }))
  }

  /**
   * Normalize objective type
   */
  normalizeObjectiveType(type) {
    const typeMap = {
      'kill': QUEST_CONFIG.OBJECTIVE_TYPES.KILL,
      'defeat': QUEST_CONFIG.OBJECTIVE_TYPES.KILL,
      'collect': QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
      'gather': QUEST_CONFIG.OBJECTIVE_TYPES.COLLECT,
      'explore': QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE,
      'discover': QUEST_CONFIG.OBJECTIVE_TYPES.EXPLORE,
      'talk_to': QUEST_CONFIG.OBJECTIVE_TYPES.TALK_TO,
      'speak': QUEST_CONFIG.OBJECTIVE_TYPES.TALK_TO,
      'craft': QUEST_CONFIG.OBJECTIVE_TYPES.CRAFT,
      'create': QUEST_CONFIG.OBJECTIVE_TYPES.CRAFT,
      'social': QUEST_CONFIG.OBJECTIVE_TYPES.SOCIAL_INTERACTION,
      'escort': QUEST_CONFIG.OBJECTIVE_TYPES.ESCORT,
      'defend': QUEST_CONFIG.OBJECTIVE_TYPES.DEFEND,
      'deliver': QUEST_CONFIG.OBJECTIVE_TYPES.DELIVER
    }

    return typeMap[type?.toLowerCase()] || QUEST_CONFIG.OBJECTIVE_TYPES.KILL
  }

  /**
   * Structure rewards properly
   */
  structureRewards(rewards, difficulty) {
    const structured = {
      base: [],
      bonus: [],
      choice: { enabled: false, options: [] }
    }

    rewards.forEach(reward => {
      const structuredReward = {
        type: this.normalizeRewardType(reward.type),
        amount: reward.amount || this.calculateDefaultRewardAmount(reward.type, difficulty),
        description: reward.description || `${reward.type} reward`,
        id: reward.id || null,
        name: reward.name || null,
        rarity: reward.rarity || this.calculateRewardRarity(difficulty)
      }

      structured.base.push(structuredReward)
    })

    // Add choice rewards for higher difficulty quests
    if (difficulty >= 4 && rewards.length > 1) {
      structured.choice.enabled = true
      structured.choice.options = rewards.slice(0, 2).map(reward => ({
        name: reward.description || 'Reward Option',
        description: `Choose this ${reward.type} reward`,
        rewards: [structuredReward]
      }))
    }

    return structured
  }

  /**
   * Normalize reward type
   */
  normalizeRewardType(type) {
    const typeMap = {
      'experience': QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
      'exp': QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
      'xp': QUEST_CONFIG.REWARD_TYPES.EXPERIENCE,
      'gold': QUEST_CONFIG.REWARD_TYPES.GOLD,
      'money': QUEST_CONFIG.REWARD_TYPES.GOLD,
      'reputation': QUEST_CONFIG.REWARD_TYPES.REPUTATION,
      'rep': QUEST_CONFIG.REWARD_TYPES.REPUTATION,
      'item': QUEST_CONFIG.REWARD_TYPES.ITEM,
      'equipment': QUEST_CONFIG.REWARD_TYPES.EQUIPMENT,
      'skill': QUEST_CONFIG.REWARD_TYPES.SKILL_POINT,
      'ability': QUEST_CONFIG.REWARD_TYPES.ABILITY,
      'title': QUEST_CONFIG.REWARD_TYPES.TITLE
    }

    return typeMap[type?.toLowerCase()] || QUEST_CONFIG.REWARD_TYPES.EXPERIENCE
  }

  /**
   * Calculate level requirement
   */
  calculateLevelRequirement(questData, params) {
    const baseLevel = Math.max(1, (questData.difficulty || params.difficulty) * 8)

    if (params.player) {
      // Adjust based on player level
      const playerLevel = params.player.stats.level
      const diff = Math.abs(playerLevel - baseLevel)

      if (diff > 5) {
        return Math.max(1, playerLevel - (baseLevel > playerLevel ? 3 : 1))
      }
    }

    return baseLevel
  }

  /**
   * Estimate quest time
   */
  estimateQuestTime(questData, difficulty) {
    const baseTime = 15 // minutes per objective
    const objectiveCount = questData.objectives?.length || 3
    const difficultyMultiplier = 0.5 + (difficulty / 7) * 1.5

    return Math.round(baseTime * objectiveCount * difficultyMultiplier)
  }

  /**
   * Calculate default reward amount
   */
  calculateDefaultRewardAmount(type, difficulty) {
    const baseAmounts = {
      [QUEST_CONFIG.REWARD_TYPES.EXPERIENCE]: 100,
      [QUEST_CONFIG.REWARD_TYPES.GOLD]: 50,
      [QUEST_CONFIG.REWARD_TYPES.REPUTATION]: 25
    }

    const base = baseAmounts[type] || 100
    return Math.round(base * difficulty * (0.8 + Math.random() * 0.4))
  }

  /**
   * Calculate reward rarity
   */
  calculateRewardRarity(difficulty) {
    if (difficulty >= 6) return 'legendary'
    if (difficulty >= 5) return 'epic'
    if (difficulty >= 4) return 'rare'
    if (difficulty >= 3) return 'uncommon'
    return 'common'
  }

  /**
   * Calculate AI confidence score
   */
  calculateConfidence(questData) {
    let confidence = 0.5 // Base confidence

    // Check for required fields
    if (questData.title && questData.title.length > 5) confidence += 0.1
    if (questData.description && questData.description.length > 50) confidence += 0.1
    if (questData.objectives && questData.objectives.length > 0) confidence += 0.1
    if (questData.story && Object.keys(questData.story).length > 0) confidence += 0.1
    if (questData.rewards && questData.rewards.length > 0) confidence += 0.1

    // Check for valid structure
    if (questData.objectives && questData.objectives.every(obj => obj.title && obj.description)) {
      confidence += 0.1
    }

    return Math.min(1.0, confidence)
  }

  /**
   * Calculate player adaptations
   */
  calculateAdaptations(player, questData) {
    return {
      difficulty: 1.0, // Could be adjusted based on player performance
      length: 1.0,     // Could be adjusted based on quest history
      complexity: 1.0   // Could be adjusted based on player skill
    }
  }

  /**
   * Generate world impact
   */
  generateWorldImpact(questData, difficulty) {
    return {
      reputation: [{
        faction: 'Local Community',
        change: difficulty * 10
      }],
      relationships: [],
      worldState: [{
        key: 'local_safety',
        value: 'improved'
      }],
      unlocks: []
    }
  }

  /**
   * Get fallback quest structure
   */
  getFallbackQuest() {
    return {
      title: "Mysterious Adventure",
      description: "An unexpected journey awaits you. The path ahead is uncertain, but fortune favors the brave.",
      objectives: [
        {
          title: "Investigate the Mystery",
          description: "Discover what secrets lie hidden in the shadows.",
          type: "explore",
          target: "unknown_location",
          required: 1
        }
      ],
      story: {
        introduction: "A strange occurrence has caught your attention.",
        background: "The local villagers have been whispering about unusual events.",
        climax: "You must face the source of the mystery.",
        resolution: "The truth is revealed and balance is restored.",
        epilogue: "Your actions have changed the course of events."
      },
      rewards: [
        {
          type: "experience",
          amount: 200,
          description: "Experience for your adventures"
        }
      ],
      difficulty: 3,
      estimatedTime: 30,
      tags: ["adventure", "mystery"]
    }
  }

  /**
   * Generate quest dialogue
   */
  async generateDialogue(questData, npcName, context) {
    try {
      const prompt = `Generate dialogue for ${npcName} in the quest "${questData.title}".

Context: ${context}

The NPC's role in the quest: ${this.getNPCRole(npcName, questData)}

Generate 3-5 dialogue lines that:
1. Advance the quest story
2. Provide relevant information
3. Match the NPC's personality
4. Are engaging and immersive

Respond with JSON format:
{
  "dialogue": [
    {
      "text": "Dialogue line",
      "emotion": "emotional_tone",
      "context": "when this is said"
    }
  ]
}`

      const response = await this.openai.chat.completions.create({
        model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
        messages: [
          { role: 'system', content: 'You are a talented dialogue writer for RPG games.' },
          { role: 'user', content: prompt }
        ],
        temperature: 0.8,
        max_tokens: 1000
      })

      const content = response.choices[0].message.content
      const jsonMatch = content.match(/\{[\s\S]*\}/)

      if (jsonMatch) {
        return JSON.parse(jsonMatch[0])
      }

      return { dialogue: [] }

    } catch (error) {
      console.error('Error generating dialogue:', error)
      return { dialogue: [] }
    }
  }

  /**
   * Get NPC role in quest
   */
  getNPCRole(npcName, questData) {
    // This would analyze the quest to determine NPC role
    return 'quest_giver' // Default
  }

  /**
   * Generate quest variations
   */
  async generateQuestVariations(baseQuest, count = 3) {
    try {
      const variations = []

      for (let i = 0; i < count; i++) {
        const prompt = `Create a variation of this quest with the same core theme but different details:

Base Quest: ${JSON.stringify(baseQuest, null, 2)}

Create a variation that:
1. Changes the specific NPCs and locations
2. Alters the approach to objectives
3. Modifies some story elements
4. Keeps the same difficulty and overall theme

Respond with valid JSON following the same structure.`

        const response = await this.openai.chat.completions.create({
          model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
          messages: [
            { role: 'system', content: this.systemPrompt },
            { role: 'user', content: prompt }
          ],
          temperature: 0.9,
          max_tokens: 3000
        })

        const content = response.choices[0].message.content
        const jsonMatch = content.match(/\{[\s\S]*\}/)

        if (jsonMatch) {
          const variation = JSON.parse(jsonMatch[0])
          variations.push(this.enhanceQuestData(variation, {
            difficulty: baseQuest.difficulty,
            type: baseQuest.type,
            category: baseQuest.category
          }))
        }
      }

      return variations

    } catch (error) {
      console.error('Error generating quest variations:', error)
      return []
    }
  }

  /**
   * Get AI generator statistics
   */
  getStatistics() {
    return {
      model: process.env.OPENAI_MODEL || 'gpt-4-turbo-preview',
      temperature: parseFloat(process.env.AI_TEMPERATURE) || 0.7,
      maxTokens: parseInt(process.env.AI_MAX_TOKENS) || 4000,
      availableTemplates: Object.keys(this.questTemplates),
      confidenceThreshold: 0.7
    }
  }
}

export default AIQuestGenerator