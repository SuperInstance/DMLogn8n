const sentiment = require('sentiment');
const natural = require('natural');
const EventEmitter = require('events');

class EmotionalIntelligenceEngine extends EventEmitter {
  constructor(options = {}) {
    super();
    this.sentimentAnalyzer = new sentiment();
    this.tokenizer = new natural.WordTokenizer();
    this.stemmer = natural.PorterStemmer;

    // Emotional state configuration
    this.emotionalStates = {
      happiness: { range: [0.5, 1.0], intensity: 0, decay: 0.02 },
      sadness: { range: [-1.0, -0.3], intensity: 0, decay: 0.03 },
      anger: { range: [-0.8, -0.2], intensity: 0, decay: 0.04 },
      fear: { range: [-0.7, -0.1], intensity: 0, decay: 0.05 },
      surprise: { range: [0.2, 0.8], intensity: 0, decay: 0.06 },
      disgust: { range: [-0.9, -0.3], intensity: 0, decay: 0.03 },
      trust: { range: [0.3, 1.0], intensity: 0, decay: 0.01 },
      anticipation: { range: [0.1, 0.7], intensity: 0, decay: 0.02 }
    };

    // Personality traits (Big Five model)
    this.personalityTraits = {
      openness: { min: 0, max: 1, current: 0.5, weight: 0.2 },
      conscientiousness: { min: 0, max: 1, current: 0.5, weight: 0.15 },
      extraversion: { min: 0, max: 1, current: 0.5, weight: 0.25 },
      agreeableness: { min: 0, max: 1, current: 0.5, weight: 0.2 },
      neuroticism: { min: 0, max: 1, current: 0.5, weight: 0.2 }
    };

    // Cultural and racial patterns
    this.culturalPatterns = new Map();
    this.initializeCulturalPatterns();

    // Memory stores
    this.emotionalMemory = new Map();
    this.conversationHistory = new Map();
    this.relationshipDynamics = new Map();

    // Configuration
    this.options = {
      emotionDecayRate: options.emotionDecayRate || 0.01,
      memoryLimit: options.memoryLimit || 1000,
      contextWindowSize: options.contextWindowSize || 10,
      empathyThreshold: options.empathyThreshold || 0.6,
      adaptationRate: options.adaptationRate || 0.1,
      ...options
    };

    // Initialize emotion decay timer
    this.startEmotionDecay();
  }

  initializeCulturalPatterns() {
    // D&D racial dialogue patterns
    this.culturalPatterns.set('dwarf', {
      speechPatterns: {
        formality: 0.7,
        directness: 0.8,
        emotionality: 0.3,
        humor: 0.4,
        loyalty: 0.9
      },
      commonPhrases: [
        'By my beard!',
        'Stone and steel!',
        'Honor guides us.',
        'The mountain stands firm.'
      ],
      emotionalTriggers: {
        disrespect: 0.8,
        betrayal: 0.9,
        craftsmanship: 0.7,
        tradition: 0.8
      }
    });

    this.culturalPatterns.set('elf', {
      speechPatterns: {
        formality: 0.8,
        directness: 0.4,
        emotionality: 0.6,
        humor: 0.3,
        loyalty: 0.7
      },
      commonPhrases: [
        'As the stars guide us.',
        'Nature\'s wisdom speaks.',
        'Time reveals all truths.',
        'Grace in all things.'
      ],
      emotionalTriggers: {
        nature: 0.9,
        beauty: 0.8,
        wisdom: 0.9,
        haste: 0.6
      }
    });

    this.culturalPatterns.set('human', {
      speechPatterns: {
        formality: 0.5,
        directness: 0.6,
        emotionality: 0.7,
        humor: 0.6,
        loyalty: 0.6
      },
      commonPhrases: [
        'Let\'s get this done.',
        'Together we stand.',
        'Fortune favors the bold.',
        'Common sense prevails.'
      ],
      emotionalTriggers: {
        ambition: 0.7,
        family: 0.8,
        community: 0.6,
        progress: 0.7
      }
    });

    this.culturalPatterns.set('orc', {
      speechPatterns: {
        formality: 0.2,
        directness: 0.9,
        emotionality: 0.8,
        humor: 0.5,
        loyalty: 0.8
      },
      commonPhrases: [
        'Strength above all!',
        'Fight with honor!',
        'No surrender!',
        'For the clan!'
      ],
      emotionalTriggers: {
        strength: 0.9,
        honor: 0.8,
        weakness: 0.7,
        betrayal: 0.9
      }
    });
  }

  async analyzeEmotion(text, speakerId, context = {}) {
    try {
      // Sentiment analysis
      const sentimentResult = this.sentimentAnalyzer.analyze(text);

      // Tokenize and extract emotional keywords
      const tokens = this.tokenizer.tokenize(text.toLowerCase());
      const emotionalKeywords = this.extractEmotionalKeywords(tokens);

      // Analyze tone and intensity
      const toneAnalysis = this.analyzeTone(text, tokens);

      // Consider cultural patterns
      const culturalInfluence = this.getCulturalInfluence(speakerId, context);

      // Calculate composite emotional state
      const emotionalState = this.calculateEmotionalState(
        sentimentResult,
        emotionalKeywords,
        toneAnalysis,
        culturalInfluence,
        context
      );

      // Update emotional memory
      this.updateEmotionalMemory(speakerId, emotionalState, text, context);

      // Trigger empathy simulation
      const empathyResponse = this.simulateEmpathy(emotionalState, speakerId);

      // Adapt personality based on interaction
      this.adaptPersonality(emotionalState, speakerId);

      // Emit emotion analysis event
      this.emit('emotionAnalyzed', {
        speakerId,
        emotionalState,
        empathyResponse,
        context,
        timestamp: new Date().toISOString()
      });

      return {
        emotionalState,
        empathyResponse,
        sentiment: sentimentResult,
        toneAnalysis,
        culturalInfluence,
        confidence: this.calculateConfidence(emotionalState)
      };

    } catch (error) {
      console.error('Error analyzing emotion:', error);
      throw new Error('Emotion analysis failed');
    }
  }

  extractEmotionalKeywords(tokens) {
    const emotionKeywords = {
      happiness: ['happy', 'joy', 'glad', 'pleased', 'delighted', 'excited', 'wonderful', 'great'],
      sadness: ['sad', 'sorrow', 'grief', 'melancholy', 'depressed', 'unhappy', 'miserable', 'heartbroken'],
      anger: ['angry', 'furious', 'rage', 'mad', 'irritated', 'annoyed', 'frustrated', 'outraged'],
      fear: ['afraid', 'scared', 'terrified', 'frightened', 'anxious', 'worried', 'nervous', 'panic'],
      surprise: ['surprised', 'amazed', 'shocked', 'astonished', 'stunned', 'bewildered', 'confused'],
      disgust: ['disgusted', 'revolted', 'repulsed', 'sickened', 'appalled', 'horror'],
      trust: ['trust', 'believe', 'faith', 'confidence', 'reliable', 'dependable', 'loyal'],
      anticipation: ['excited', 'eager', 'looking forward', 'expect', 'hope', 'anticipate', 'await']
    };

    const foundKeywords = {};
    for (const [emotion, keywords] of Object.entries(emotionKeywords)) {
      foundKeywords[emotion] = tokens.filter(token => keywords.includes(token));
    }

    return foundKeywords;
  }

  analyzeTone(text, tokens) {
    const tone = {
      intensity: this.calculateIntensity(tokens),
      formality: this.calculateFormality(text),
      urgency: this.calculateUrgency(tokens),
      sarcasm: this.detectSarcasm(text, tokens),
      questioning: this.detectQuestions(text),
      emotional: this.calculateEmotionalContent(tokens)
    };

    return tone;
  }

  calculateIntensity(tokens) {
    const intensifiers = ['very', 'extremely', 'incredibly', 'absolutely', 'completely', 'totally', 'really'];
    const diminishers = ['slightly', 'somewhat', 'rather', 'quite', 'kinda', 'sorta'];

    let intensity = 0.5; // Base intensity
    tokens.forEach(token => {
      if (intensifiers.includes(token)) intensity += 0.1;
      if (diminishers.includes(token)) intensity -= 0.1;
    });

    // Exclamation points increase intensity
    const exclamations = (text.match(/!/g) || []).length;
    intensity += exclamations * 0.1;

    return Math.min(1.0, Math.max(0.0, intensity));
  }

  calculateFormality(text) {
    const formalWords = ['please', 'thank you', 'would', 'could', 'sir', 'madam', 'regards', 'sincerely'];
    const informalWords = ['hey', 'yo', 'what\'s up', 'gonna', 'wanna', 'kinda', 'sorta'];

    const words = text.toLowerCase().split(/\s+/);
    let formalScore = 0.5;

    words.forEach(word => {
      if (formalWords.some(fw => word.includes(fw))) formalScore += 0.1;
      if (informalWords.some(iw => word.includes(iw))) formalScore -= 0.1;
    });

    return Math.min(1.0, Math.max(0.0, formalScore));
  }

  calculateUrgency(tokens) {
    const urgencyWords = ['urgent', 'immediately', 'now', 'quickly', 'fast', 'hurry', 'emergency', 'asap'];
    const urgencyCount = tokens.filter(token => urgencyWords.includes(token)).length;
    return Math.min(1.0, urgencyCount * 0.2);
  }

  detectSarcasm(text, tokens) {
    const sarcasmIndicators = ['yeah right', 'sure', 'obviously', 'clearly', 'totally'];
    const textLower = text.toLowerCase();

    let sarcasmScore = 0;
    sarcasmIndicators.forEach(indicator => {
      if (textLower.includes(indicator)) sarcasmScore += 0.3;
    });

    // Check for mismatch between sentiment and intensifiers
    const positiveWords = ['good', 'great', 'wonderful', 'amazing'];
    const negativeWords = ['bad', 'terrible', 'awful', 'horrible'];

    const hasPositive = tokens.some(t => positiveWords.includes(t));
    const hasNegative = tokens.some(t => negativeWords.includes(t));

    if (hasPositive && hasNegative) sarcasmScore += 0.4;

    return Math.min(1.0, sarcasmScore);
  }

  detectQuestions(text) {
    const questionCount = (text.match(/\?/g) || []).length;
    const questionWords = ['who', 'what', 'when', 'where', 'why', 'how', 'which', 'whose'];
    const tokens = text.toLowerCase().split(/\s+/);
    const questionWordCount = tokens.filter(token => questionWords.includes(token)).length;

    return Math.min(1.0, (questionCount + questionWordCount * 0.5) * 0.3);
  }

  calculateEmotionalContent(tokens) {
    const emotionWords = [
      'feel', 'feeling', 'emotion', 'happy', 'sad', 'angry', 'scared', 'love', 'hate',
      'joy', 'sorrow', 'excitement', 'fear', 'hope', 'despair', 'passion', 'calm'
    ];

    const emotionWordCount = tokens.filter(token => emotionWords.includes(token)).length;
    return Math.min(1.0, emotionWordCount * 0.15);
  }

  getCulturalInfluence(speakerId, context) {
    const culturalPattern = this.culturalPatterns.get(context.race || 'human');
    if (!culturalPattern) return { speechPatterns: {}, triggers: {} };

    return {
      speechPatterns: culturalPattern.speechPatterns,
      emotionalTriggers: culturalPattern.emotionalTriggers,
      commonPhrases: culturalPattern.commonPhrases
    };
  }

  calculateEmotionalState(sentimentResult, emotionalKeywords, toneAnalysis, culturalInfluence, context) {
    const emotionalState = {};

    // Calculate base emotions from sentiment
    const sentimentScore = sentimentResult.score / Math.max(sentimentResult.comparative * 10, 1);

    for (const [emotion, config] of Object.entries(this.emotionalStates)) {
      let intensity = 0;

      // Base calculation from sentiment range
      if (sentimentScore >= config.range[0] && sentimentScore <= config.range[1]) {
        intensity = Math.abs(sentimentScore);
      }

      // Adjust based on emotional keywords
      const keywordCount = emotionalKeywords[emotion]?.length || 0;
      intensity += keywordCount * 0.1;

      // Apply tone analysis
      intensity *= (1 + toneAnalysis.intensity * 0.3);
      intensity *= (1 + toneAnalysis.emotional * 0.2);

      // Apply cultural influence
      if (culturalInfluence.speechPatterns.emotionality) {
        intensity *= culturalInfluence.speechPatterns.emotionality;
      }

      // Apply personality traits
      intensity *= this.getPersonalityInfluence(emotion);

      // Update emotional state with decay
      this.emotionalStates[emotion].intensity =
        this.emotionalStates[emotion].intensity * (1 - this.emotionalStates[emotion].decay) +
        intensity * this.options.adaptationRate;

      emotionalState[emotion] = this.emotionalStates[emotion].intensity;
    }

    return emotionalState;
  }

  getPersonalityInfluence(emotion) {
    const influence = {
      happiness: this.personalityTraits.extraversion.current * 0.3 +
                 (1 - this.personalityTraits.neuroticism.current) * 0.4,
      sadness: this.personalityTraits.neuroticism.current * 0.5,
      anger: this.personalityTraits.neuroticism.current * 0.4 +
             (1 - this.personalityTraits.agreeableness.current) * 0.3,
      fear: this.personalityTraits.neuroticism.current * 0.6,
      surprise: this.personalityTraits.openness.current * 0.4,
      disgust: this.personalityTraits.conscientiousness.current * 0.3,
      trust: this.personalityTraits.agreeableness.current * 0.5,
      anticipation: this.personalityTraits.openness.current * 0.3
    };

    return influence[emotion] || 1.0;
  }

  updateEmotionalMemory(speakerId, emotionalState, text, context) {
    if (!this.emotionalMemory.has(speakerId)) {
      this.emotionalMemory.set(speakerId, []);
    }

    const memory = {
      timestamp: new Date().toISOString(),
      emotionalState: { ...emotionalState },
      text,
      context,
      mood: this.calculateMood(emotionalState)
    };

    const memories = this.emotionalMemory.get(speakerId);
    memories.push(memory);

    // Limit memory size
    if (memories.length > this.options.memoryLimit) {
      memories.shift();
    }
  }

  calculateMood(emotionalState) {
    const positiveEmotions = emotionalState.happiness + emotionalState.trust + emotionalState.anticipation;
    const negativeEmotions = emotionalState.sadness + emotionalState.anger + emotionalState.fear + emotionalState.disgust;

    return positiveEmotions - negativeEmotions;
  }

  simulateEmpathy(emotionalState, speakerId) {
    const empathyLevel = this.calculateEmpathyLevel(speakerId);
    const dominantEmotion = this.getDominantEmotion(emotionalState);

    if (empathyLevel < this.options.empathyThreshold) {
      return null;
    }

    const empathyResponse = {
      detectedEmotion: dominantEmotion,
      intensity: emotionalState[dominantEmotion],
      empathyLevel,
      responseStrategy: this.determineEmpathyStrategy(dominantEmotion, emotionalState[dominantEmotion]),
      suggestedResponses: this.generateEmpatheticResponses(dominantEmotion, emotionalState[dominantEmotion])
    };

    return empathyResponse;
  }

  calculateEmpathyLevel(speakerId) {
    const relationship = this.relationshipDynamics.get(speakerId);
    const baseEmpathy = 0.5;
    const relationshipBonus = relationship ? relationship.trust * 0.3 : 0;
    const personalityBonus = this.personalityTraits.agreeableness.current * 0.2;

    return Math.min(1.0, baseEmpathy + relationshipBonus + personalityBonus);
  }

  getDominantEmotion(emotionalState) {
    return Object.entries(emotionalState).reduce((dominant, [emotion, intensity]) =>
      intensity > emotionalState[dominant] ? emotion : dominant,
      Object.keys(emotionalState)[0]
    );
  }

  determineEmpathyStrategy(emotion, intensity) {
    const strategies = {
      happiness: intensity > 0.7 ? 'enthusiastic' : 'supportive',
      sadness: intensity > 0.7 ? 'comforting' : 'supportive',
      anger: intensity > 0.7 ? 'deescalating' : 'understanding',
      fear: intensity > 0.7 ? 'reassuring' : 'supportive',
      surprise: intensity > 0.7 ? 'engaged' : 'acknowledging',
      disgust: intensity > 0.7 ? 'validating' : 'understanding',
      trust: 'reciprocal',
      anticipation: 'engaged'
    };

    return strategies[emotion] || 'neutral';
  }

  generateEmpatheticResponses(emotion, intensity) {
    const responseTemplates = {
      happiness: [
        "I can hear the excitement in your voice! Tell me more.",
        "That sounds wonderful! I'm genuinely happy for you.",
        "Your enthusiasm is contagious! What else happened?"
      ],
      sadness: [
        "I can hear how difficult this is for you. I'm here to listen.",
        "That sounds really tough. You don't have to go through this alone.",
        "I understand this hurts. Take your time to process this."
      ],
      anger: [
        "I can understand why you'd feel angry about this. Let's work through it.",
        "Your feelings are valid. What do you think would help right now?",
        "I hear your frustration. Let's find a constructive way forward."
      ],
      fear: [
        "That sounds scary. You're safe to talk about this with me.",
        "I understand your concern. Let's think through this together.",
        "Your fear makes sense given the situation. What would help you feel more secure?"
      ],
      surprise: [
        "Wow! That's unexpected! Tell me everything.",
        "I'm intrigued! What happened next?",
        "That's fascinating! I didn't see that coming."
      ]
    };

    const templates = responseTemplates[emotion] || ["I understand.", "Tell me more.", "How does that make you feel?"];
    return templates.slice(0, Math.min(3, Math.ceil(intensity * 3) + 1));
  }

  adaptPersonality(emotionalState, speakerId) {
    const relationship = this.relationshipDynamics.get(speakerId) || { trust: 0.5, familiarity: 0 };

    // Gradually adapt personality based on interactions
    if (emotionalState.happiness > 0.6) {
      this.personalityTraits.extraversion.current = Math.min(1.0,
        this.personalityTraits.extraversion.current + this.options.adaptationRate * 0.1);
    }

    if (emotionalState.trust > 0.6) {
      this.personalityTraits.agreeableness.current = Math.min(1.0,
        this.personalityTraits.agreeableness.current + this.options.adaptationRate * 0.1);
    }

    // Update relationship dynamics
    if (!this.relationshipDynamics.has(speakerId)) {
      this.relationshipDynamics.set(speakerId, { trust: 0.5, familiarity: 0, lastInteraction: new Date() });
    }

    const currentRelationship = this.relationshipDynamics.get(speakerId);
    currentRelationship.familiarity = Math.min(1.0, currentRelationship.familiarity + this.options.adaptationRate);
    currentRelationship.trust = Math.min(1.0, currentRelationship.trust + emotionalState.trust * this.options.adaptationRate);
    currentRelationship.lastInteraction = new Date();
  }

  calculateConfidence(emotionalState) {
    const totalIntensity = Object.values(emotionalState).reduce((sum, intensity) => sum + intensity, 0);
    const maxIntensity = Math.max(...Object.values(emotionalState));
    const clarity = maxIntensity / (totalIntensity || 1);

    return Math.min(1.0, clarity * (totalIntensity > 0.5 ? 1.0 : totalIntensity * 2));
  }

  startEmotionDecay() {
    setInterval(() => {
      for (const [emotion, config] of Object.entries(this.emotionalStates)) {
        config.intensity = Math.max(0, config.intensity - config.decay);
      }
      this.emit('emotionDecay', { timestamp: new Date().toISOString() });
    }, 5000); // Decay every 5 seconds
  }

  // API Methods
  getEmotionalState(speakerId) {
    return this.emotionalMemory.get(speakerId) || [];
  }

  getRelationshipDynamics(speakerId) {
    return this.relationshipDynamics.get(speakerId) || { trust: 0.5, familiarity: 0 };
  }

  getPersonalityProfile() {
    return { ...this.personalityTraits };
  }

  setPersonalityTrait(trait, value) {
    if (this.personalityTraits[trait]) {
      this.personalityTraits[trait].current = Math.max(this.personalityTraits[trait].min,
        Math.min(this.personalityTraits[trait].max, value));
    }
  }

  reset() {
    for (const config of Object.values(this.emotionalStates)) {
      config.intensity = 0;
    }
    this.emotionalMemory.clear();
    this.conversationHistory.clear();
    this.relationshipDynamics.clear();
  }
}

module.exports = EmotionalIntelligenceEngine;