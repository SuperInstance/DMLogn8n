const EventEmitter = require('events');
const { v4: uuidv4 } = require('uuid');
const moment = require('moment');

class ContextAwareConversationManager extends EventEmitter {
  constructor(options = {}) {
    super();

    // Memory stores
    this.conversations = new Map(); // Active conversations
    this.shortTermMemory = new Map(); // Recent context
    this.longTermMemory = new Map(); // Historical data
    this.environmentalContext = new Map(); // Environmental awareness
    this.relationshipContext = new Map(); // Character relationships
    this.campaignKnowledge = new Map(); // Campaign information
    this.worldEvents = new Map(); // Real-time world events

    // Configuration
    this.options = {
      maxConversations: options.maxConversations || 100,
      shortTermMemoryLimit: options.shortTermMemoryLimit || 50,
      longTermMemoryLimit: options.longTermMemoryLimit || 1000,
      contextWindowSize: options.contextWindowSize || 10,
      relationshipDecayRate: options.relationshipDecayRate || 0.001,
      environmentalUpdateInterval: options.environmentalUpdateInterval || 30000,
      worldEventCheckInterval: options.worldEventCheckInterval || 60000,
      ...options
    };

    // Initialize timers
    this.startTimers();

    // Conversation state management
    this.conversationStates = {
      INITIATING: 'initiating',
      ACTIVE: 'active',
      PAUSED: 'paused',
      RESUMING: 'resuming',
      CONCLUDING: 'concluding',
      CONCLUDED: 'concluded'
    };

    // Context types
    this.contextTypes = {
      PERSONAL: 'personal',
      ENVIRONMENTAL: 'environmental',
      RELATIONSHIP: 'relationship',
      CAMPAIGN: 'campaign',
      TEMPORAL: 'temporal',
      EMOTIONAL: 'emotional',
      CULTURAL: 'cultural'
    };
  }

  startTimers() {
    // Environmental context update timer
    setInterval(() => {
      this.updateEnvironmentalContext();
    }, this.options.environmentalUpdateInterval);

    // World events check timer
    setInterval(() => {
      this.checkWorldEvents();
    }, this.options.worldEventCheckInterval);

    // Relationship decay timer
    setInterval(() => {
      this.updateRelationshipDecay();
    }, 3600000); // Every hour
  }

  async initiateConversation(participants, context = {}) {
    try {
      const conversationId = uuidv4();
      const conversation = {
        id: conversationId,
        participants,
        state: this.conversationStates.INITIATING,
        startTime: new Date().toISOString(),
        endTime: null,
        context: {
          ...context,
          initialContext: this.buildInitialContext(participants, context)
        },
        messages: [],
        metadata: {
          turns: 0,
          topics: [],
          emotionalTrajectory: [],
          keyMoments: []
        }
      };

      this.conversations.set(conversationId, conversation);

      // Initialize short-term memory for each participant
      participants.forEach(participant => {
        if (!this.shortTermMemory.has(participant.id)) {
          this.shortTermMemory.set(participant.id, []);
        }
      });

      // Build contextual awareness
      const fullContext = await this.buildContextualAwareness(conversationId);

      // Update conversation state
      conversation.state = this.conversationStates.ACTIVE;

      this.emit('conversationInitiated', {
        conversationId,
        participants,
        context: fullContext,
        timestamp: new Date().toISOString()
      });

      return {
        conversationId,
        context: fullContext,
        participants,
        suggestions: this.generateConversationSuggestions(fullContext)
      };

    } catch (error) {
      console.error('Error initiating conversation:', error);
      throw new Error('Failed to initiate conversation');
    }
  }

  async processMessage(conversationId, message, speakerId, additionalContext = {}) {
    try {
      const conversation = this.conversations.get(conversationId);
      if (!conversation) {
        throw new Error('Conversation not found');
      }

      // Create message object
      const messageObject = {
        id: uuidv4(),
        speakerId,
        content: message,
        timestamp: new Date().toISOString(),
        context: {
          ...additionalContext,
          environmental: this.getCurrentEnvironmentalContext(),
          relational: this.getRelationshipContext(speakerId, conversation.participants),
          campaign: this.getCampaignContext(conversation.context.campaignId),
          temporal: this.getTemporalContext()
        },
        processed: false
      };

      // Add message to conversation
      conversation.messages.push(messageObject);
      conversation.metadata.turns++;

      // Update short-term memory
      this.updateShortTermMemory(speakerId, messageObject);

      // Extract and update topics
      this.updateConversationTopics(conversation, messageObject);

      // Update context based on message
      const updatedContext = await this.updateConversationContext(conversationId, messageObject);

      // Generate response suggestions
      const responseSuggestions = this.generateResponseSuggestions(
        conversationId,
        messageObject,
        updatedContext
      );

      // Check for key moments
      this.checkForKeyMoments(conversation, messageObject);

      // Mark message as processed
      messageObject.processed = true;

      this.emit('messageProcessed', {
        conversationId,
        message: messageObject,
        context: updatedContext,
        suggestions: responseSuggestions,
        timestamp: new Date().toISOString()
      });

      return {
        message: messageObject,
        context: updatedContext,
        suggestions: responseSuggestions,
        conversationState: conversation.state
      };

    } catch (error) {
      console.error('Error processing message:', error);
      throw new Error('Failed to process message');
    }
  }

  buildInitialContext(participants, providedContext) {
    const initialContext = {
      participants: participants.map(p => ({
        id: p.id,
        name: p.name,
        role: p.role,
        race: p.race || 'human',
        class: p.class,
        background: p.background,
        disposition: p.disposition || 'neutral'
      })),
      location: providedContext.location || {},
      time: providedContext.time || {},
      weather: providedContext.weather || {},
      atmosphere: providedContext.atmosphere || 'neutral',
      objectives: providedContext.objectives || [],
      constraints: providedContext.constraints || []
    };

    // Add relationship context between participants
    initialContext.relationships = this.buildParticipantRelationships(participants);

    return initialContext;
  }

  buildParticipantRelationships(participants) {
    const relationships = {};

    participants.forEach(participant => {
      relationships[participant.id] = {};

      participants.forEach(otherParticipant => {
        if (participant.id !== otherParticipant.id) {
          const existingRelationship = this.relationshipContext.get(
            `${participant.id}-${otherParticipant.id}`
          );

          relationships[participant.id][otherParticipant.id] = existingRelationship || {
            trust: 0.5,
            familiarity: 0.3,
            history: [],
            lastInteraction: null,
            disposition: 'neutral'
          };
        }
      });
    });

    return relationships;
  }

  async buildContextualAwareness(conversationId) {
    const conversation = this.conversations.get(conversationId);
    const fullContext = {
      conversation: {
        id: conversationId,
        state: conversation.state,
        duration: this.calculateConversationDuration(conversation),
        participants: conversation.participants,
        turnCount: conversation.metadata.turns
      },
      environmental: this.getCurrentEnvironmentalContext(),
      temporal: this.getTemporalContext(),
      campaign: this.getCampaignContext(conversation.context.campaignId),
      social: this.getSocialContext(conversation.participants),
      historical: this.getHistoricalContext(conversation.participants),
      worldEvents: this.getRelevantWorldEvents(conversation.context.location)
    };

    return fullContext;
  }

  updateShortTermMemory(speakerId, messageObject) {
    if (!this.shortTermMemory.has(speakerId)) {
      this.shortTermMemory.set(speakerId, []);
    }

    const memory = this.shortTermMemory.get(speakerId);
    memory.push({
      type: 'message',
      data: messageObject,
      timestamp: new Date().toISOString()
    });

    // Limit memory size
    if (memory.length > this.options.shortTermMemoryLimit) {
      memory.shift();
    }
  }

  updateConversationTopics(conversation, messageObject) {
    const topics = this.extractTopics(messageObject.content);

    topics.forEach(topic => {
      if (!conversation.metadata.topics.includes(topic)) {
        conversation.metadata.topics.push(topic);
      }
    });
  }

  extractTopics(text) {
    // Simple topic extraction - can be enhanced with NLP
    const dndTopics = [
      'quest', 'battle', 'magic', 'dragon', 'dungeon', 'treasure', 'monster',
      'party', 'guild', 'kingdom', 'prophecy', 'artifact', 'curse', 'blessing',
      'travel', 'inn', 'tavern', 'shop', 'training', 'level', 'experience'
    ];

    const topics = [];
    const textLower = text.toLowerCase();

    dndTopics.forEach(topic => {
      if (textLower.includes(topic)) {
        topics.push(topic);
      }
    });

    return topics;
  }

  async updateConversationContext(conversationId, messageObject) {
    const conversation = this.conversations.get(conversationId);

    // Update conversation context
    conversation.context.lastMessage = messageObject;
    conversation.context.lastUpdate = new Date().toISOString();

    // Update environmental context if mentioned
    this.updateEnvironmentalContextFromMessage(messageObject);

    // Update relationship context
    this.updateRelationshipContextFromMessage(conversation, messageObject);

    // Update campaign context if relevant
    this.updateCampaignContextFromMessage(conversation, messageObject);

    return await this.buildContextualAwareness(conversationId);
  }

  updateEnvironmentalContextFromMessage(messageObject) {
    const environmentalKeywords = {
      weather: ['rain', 'sun', 'snow', 'wind', 'storm', 'clear', 'cloudy', 'fog'],
      location: ['forest', 'mountain', 'city', 'dungeon', 'cave', 'castle', 'village'],
      time: ['morning', 'afternoon', 'evening', 'night', 'dawn', 'dusk'],
      atmosphere: ['tense', 'relaxed', 'hostile', 'friendly', 'mysterious', 'chaotic']
    };

    const content = messageObject.content.toLowerCase();

    Object.entries(environmentalKeywords).forEach(([type, keywords]) => {
      keywords.forEach(keyword => {
        if (content.includes(keyword)) {
          this.updateEnvironmentalContext(type, keyword, messageObject.timestamp);
        }
      });
    });
  }

  updateEnvironmentalContext(type, value, timestamp) {
    if (!this.environmentalContext.has(type)) {
      this.environmentalContext.set(type, []);
    }

    const context = this.environmentalContext.get(type);
    context.push({
      value,
      timestamp,
      confidence: 0.8
    });

    // Keep only recent context
    const cutoff = moment(timestamp).subtract(1, 'hour').toISOString();
    const filtered = context.filter(c => c.timestamp > cutoff);
    this.environmentalContext.set(type, filtered);
  }

  getCurrentEnvironmentalContext() {
    const context = {};

    for (const [type, data] of this.environmentalContext) {
      if (data.length > 0) {
        // Get the most recent and most confident value
        const sorted = data.sort((a, b) => {
          if (b.confidence !== a.confidence) return b.confidence - a.confidence;
          return new Date(b.timestamp) - new Date(a.timestamp);
        });
        context[type] = sorted[0].value;
      }
    }

    return context;
  }

  updateRelationshipContextFromMessage(conversation, messageObject) {
    const speakerId = messageObject.speakerId;
    const otherParticipants = conversation.participants.filter(p => p.id !== speakerId);

    otherParticipants.forEach(participant => {
      const relationshipKey = `${speakerId}-${participant.id}`;
      let relationship = this.relationshipContext.get(relationshipKey);

      if (!relationship) {
        relationship = {
          trust: 0.5,
          familiarity: 0.3,
          history: [],
          lastInteraction: null,
          disposition: 'neutral'
        };
        this.relationshipContext.set(relationshipKey, relationship);
      }

      // Update relationship based on message content
      const sentimentAnalysis = this.analyzeMessageSentiment(messageObject.content);
      relationship.trust = Math.max(0, Math.min(1,
        relationship.trust + sentimentAnalysis.positive * 0.01 - sentimentAnalysis.negative * 0.01
      ));

      relationship.familiarity = Math.min(1, relationship.familiarity + 0.001);
      relationship.lastInteraction = messageObject.timestamp;

      relationship.history.push({
        type: 'message',
        timestamp: messageObject.timestamp,
        sentiment: sentimentAnalysis,
        topic: messageObject.content.substring(0, 50) // Preview
      });

      // Limit history size
      if (relationship.history.length > 100) {
        relationship.history.shift();
      }
    });
  }

  analyzeMessageSentiment(content) {
    // Simple sentiment analysis - can be enhanced
    const positiveWords = ['good', 'great', 'happy', 'friend', 'help', 'thank', 'love', 'excellent'];
    const negativeWords = ['bad', 'terrible', 'hate', 'enemy', 'kill', 'destroy', 'angry', 'sad'];

    const words = content.toLowerCase().split(/\s+/);
    let positive = 0;
    let negative = 0;

    words.forEach(word => {
      if (positiveWords.some(pw => word.includes(pw))) positive++;
      if (negativeWords.some(nw => word.includes(nw))) negative++;
    });

    return { positive, negative, neutral: words.length - positive - negative };
  }

  updateCampaignContextFromMessage(conversation, messageObject) {
    const campaignId = conversation.context.campaignId;
    if (!campaignId) return;

    // Extract campaign-relevant information
    const campaignKeywords = ['quest', 'objective', 'goal', 'mission', 'task', 'duty'];
    const content = messageObject.content.toLowerCase();

    if (campaignKeywords.some(keyword => content.includes(keyword))) {
      // Update campaign knowledge
      this.updateCampaignKnowledge(campaignId, messageObject);
    }
  }

  updateCampaignKnowledge(campaignId, messageObject) {
    if (!this.campaignKnowledge.has(campaignId)) {
      this.campaignKnowledge.set(campaignId, {
        objectives: [],
        discoveries: [],
        characterProgress: new Map(),
        worldStateChanges: [],
        timeline: []
      });
    }

    const knowledge = this.campaignKnowledge.get(campaignId);
    knowledge.timeline.push({
      type: 'dialogue',
      timestamp: messageObject.timestamp,
      speaker: messageObject.speakerId,
      content: messageObject.content.substring(0, 100)
    });
  }

  getCampaignContext(campaignId) {
    if (!campaignId) return null;

    return this.campaignKnowledge.get(campaignId) || null;
  }

  getRelationshipContext(speakerId, participants) {
    const relationships = {};

    participants.forEach(participant => {
      if (participant.id !== speakerId) {
        const relationshipKey = `${speakerId}-${participant.id}`;
        relationships[participant.id] = this.relationshipContext.get(relationshipKey) || {
          trust: 0.5,
          familiarity: 0.3,
          disposition: 'neutral'
        };
      }
    });

    return relationships;
  }

  getSocialContext(participants) {
    const socialContext = {
      groupDynamics: this.analyzeGroupDynamics(participants),
      powerStructure: this.analyzePowerStructure(participants),
      communicationPatterns: this.analyzeCommunicationPatterns(participants)
    };

    return socialContext;
  }

  analyzeGroupDynamics(participants) {
    // Analyze how the group interacts
    let totalTrust = 0;
    let totalFamiliarity = 0;
    let relationshipCount = 0;

    participants.forEach(participant => {
      participants.forEach(otherParticipant => {
        if (participant.id !== otherParticipant.id) {
          const relationship = this.relationshipContext.get(
            `${participant.id}-${otherParticipant.id}`
          );
          if (relationship) {
            totalTrust += relationship.trust;
            totalFamiliarity += relationship.familiarity;
            relationshipCount++;
          }
        }
      });
    });

    return {
      averageTrust: relationshipCount > 0 ? totalTrust / relationshipCount : 0.5,
      averageFamiliarity: relationshipCount > 0 ? totalFamiliarity / relationshipCount : 0.3,
      cohesion: relationshipCount > 0 ? (totalTrust + totalFamiliarity) / (relationshipCount * 2) : 0.4
    };
  }

  analyzePowerStructure(participants) {
    // Analyze power dynamics based on roles and relationships
    const powerScores = {};

    participants.forEach(participant => {
      let powerScore = 0.5; // Base power

      // Adjust based on role
      if (participant.role === 'leader') powerScore += 0.3;
      if (participant.role === 'healer') powerScore += 0.1;
      if (participant.role === 'tank') powerScore += 0.1;

      // Adjust based on relationships
      participants.forEach(other => {
        if (other.id !== participant.id) {
          const relationship = this.relationshipContext.get(`${other.id}-${participant.id}`);
          if (relationship && relationship.trust > 0.7) {
            powerScore += 0.05; // Trusted by others
          }
        }
      });

      powerScores[participant.id] = Math.min(1.0, powerScore);
    });

    return powerScores;
  }

  analyzeCommunicationPatterns(participants) {
    // Analyze how participants communicate with each other
    return {
      dominance: this.calculateCommunicationDominance(participants),
      responsiveness: this.calculateResponsiveness(participants),
      topics: this.getCommonTopics(participants)
    };
  }

  calculateCommunicationDominance(participants) {
    // This would be based on historical conversation data
    return {};
  }

  calculateResponsiveness(participants) {
    // This would analyze response times and engagement
    return {};
  }

  getCommonTopics(participants) {
    // Find topics commonly discussed by the group
    return [];
  }

  getHistoricalContext(participants) {
    const historicalContext = {
      pastInteractions: new Map(),
      sharedExperiences: [],
      characterDevelopment: new Map()
    };

    participants.forEach(participant => {
      const history = this.longTermMemory.get(participant.id);
      if (history) {
        historicalContext.pastInteractions.set(participant.id, history.slice(-10)); // Last 10 interactions
      }
    });

    return historicalContext;
  }

  getTemporalContext() {
    return {
      currentTime: new Date().toISOString(),
      sessionTime: moment().format('HH:mm'),
      date: moment().format('YYYY-MM-DD'),
      dayOfWeek: moment().format('dddd'),
      season: this.getCurrentSeason(),
      timeOfDay: this.getTimeOfDay()
    };
  }

  getCurrentSeason() {
    const month = moment().month();
    if (month >= 2 && month <= 4) return 'spring';
    if (month >= 5 && month <= 7) return 'summer';
    if (month >= 8 && month <= 10) return 'fall';
    return 'winter';
  }

  getTimeOfDay() {
    const hour = moment().hour();
    if (hour >= 6 && hour < 12) return 'morning';
    if (hour >= 12 && hour < 18) return 'afternoon';
    if (hour >= 18 && hour < 22) return 'evening';
    return 'night';
  }

  getRelevantWorldEvents(location) {
    // Get world events relevant to current location
    const events = [];

    for (const [eventId, event] of this.worldEvents) {
      if (this.isEventRelevant(event, location)) {
        events.push(event);
      }
    }

    return events;
  }

  isEventRelevant(event, location) {
    // Check if event is relevant to current location
    if (!event.location || !location) return true;

    return event.location.region === location.region ||
           event.location.city === location.city ||
           event.location.area === location.area;
  }

  checkWorldEvents() {
    // This would integrate with external world event systems
    // For now, we'll simulate some events
    const simulatedEvent = {
      id: uuidv4(),
      type: 'world_event',
      title: 'Merchant caravan arrives',
      description: 'A large merchant caravan has arrived in the nearby town.',
      location: { region: 'current' },
      timestamp: new Date().toISOString(),
      impact: 'economic'
    };

    this.worldEvents.set(simulatedEvent.id, simulatedEvent);
  }

  updateEnvironmentalContext() {
    // Periodic update of environmental context
    // This would integrate with weather APIs, game state, etc.
  }

  updateRelationshipDecay() {
    // Apply decay to relationship values over time
    for (const [key, relationship] of this.relationshipContext) {
      relationship.trust = Math.max(0.1, relationship.trust - this.options.relationshipDecayRate);
      relationship.familiarity = Math.max(0.1, relationship.familiarity - this.options.relationshipDecayRate);
    }
  }

  generateResponseSuggestions(conversationId, messageObject, context) {
    const suggestions = [];

    // Generate contextual response suggestions
    suggestions.push(...this.generateContextualResponses(messageObject, context));

    // Generate emotionally appropriate responses
    suggestions.push(...this.generateEmotionalResponses(messageObject, context));

    // Generate goal-oriented responses
    suggestions.push(...this.generateGoalOrientedResponses(messageObject, context));

    // Sort by relevance and return top suggestions
    return suggestions.sort((a, b) => b.relevance - a.relevance).slice(0, 5);
  }

  generateContextualResponses(messageObject, context) {
    const responses = [];
    const content = messageObject.content.toLowerCase();

    // Question responses
    if (content.includes('?')) {
      responses.push({
        type: 'answer',
        text: 'Let me help you with that question.',
        relevance: 0.8,
        emotionalTone: 'helpful'
      });
    }

    // Request responses
    if (content.includes('help') || content.includes('need')) {
      responses.push({
        type: 'assistance',
        text: 'I\'m here to help. What do you need?',
        relevance: 0.9,
        emotionalTone: 'supportive'
      });
    }

    // Information sharing
    if (content.includes('tell') || content.includes('explain')) {
      responses.push({
        type: 'information',
        text: 'I understand you\'d like more information.',
        relevance: 0.7,
        emotionalTone: 'informative'
      });
    }

    return responses;
  }

  generateEmotionalResponses(messageObject, context) {
    const responses = [];
    const sentiment = this.analyzeMessageSentiment(messageObject.content);

    if (sentiment.positive > sentiment.negative) {
      responses.push({
        type: 'positive',
        text: 'That\'s wonderful to hear!',
        relevance: 0.7,
        emotionalTone: 'happy'
      });
    } else if (sentiment.negative > sentiment.positive) {
      responses.push({
        type: 'supportive',
        text: 'I understand. I\'m here to support you.',
        relevance: 0.8,
        emotionalTone: 'empathetic'
      });
    }

    return responses;
  }

  generateGoalOrientedResponses(messageObject, context) {
    const responses = [];

    // Quest-related responses
    if (context.campaign && context.campaign.objectives.length > 0) {
      responses.push({
        type: 'quest',
        text: 'How does this relate to our current objectives?',
        relevance: 0.6,
        emotionalTone: 'focused'
      });
    }

    return responses;
  }

  generateConversationSuggestions(context) {
    const suggestions = {
      openingLines: this.generateOpeningLines(context),
      topics: this.generateTopicSuggestions(context),
      objectives: this.generateObjectiveSuggestions(context)
    };

    return suggestions;
  }

  generateOpeningLines(context) {
    const lines = [
      'It\'s good to see you all gathered here.',
      'I\'ve been meaning to speak with you about something important.',
      'There\'s something we need to discuss.',
      'Welcome, friends. I have news to share.'
    ];

    return lines.map(line => ({
      text: line,
      context: 'greeting',
      appropriateness: 0.8
    }));
  }

  generateTopicSuggestions(context) {
    const topics = [
      'Current quest progress',
      'Recent discoveries',
      'Party strategy',
      'Equipment and supplies',
      'Future plans'
    ];

    return topics.map(topic => ({
      topic,
      relevance: 0.7
    }));
  }

  generateObjectiveSuggestions(context) {
    return [
      'Gather information',
      'Build party cohesion',
      'Plan next steps',
      'Resolve conflicts',
      'Share knowledge'
    ];
  }

  checkForKeyMoments(conversation, messageObject) {
    const content = messageObject.content.toLowerCase();
    const keyMomentIndicators = [
      'important', 'critical', 'urgent', 'secret', 'truth',
      'discovery', 'revelation', 'decision', 'choice', 'destiny'
    ];

    const hasKeyMoment = keyMomentIndicators.some(indicator => content.includes(indicator));

    if (hasKeyMoment) {
      const keyMoment = {
        type: 'key_moment',
        message: messageObject,
        timestamp: messageObject.timestamp,
        significance: this.calculateSignificance(content)
      };

      conversation.metadata.keyMoments.push(keyMoment);

      this.emit('keyMoment', {
        conversationId: conversation.id,
        keyMoment,
        timestamp: new Date().toISOString()
      });
    }
  }

  calculateSignificance(content) {
    const highSignificanceWords = ['destiny', 'prophecy', 'chosen', 'fate', 'legend'];
    const mediumSignificanceWords = ['important', 'critical', 'urgent', 'secret'];

    let significance = 0.5; // Base significance

    highSignificanceWords.forEach(word => {
      if (content.includes(word)) significance += 0.3;
    });

    mediumSignificanceWords.forEach(word => {
      if (content.includes(word)) significance += 0.2;
    });

    return Math.min(1.0, significance);
  }

  calculateConversationDuration(conversation) {
    const start = moment(conversation.startTime);
    const end = conversation.endTime ? moment(conversation.endTime) : moment();
    return end.diff(start, 'seconds');
  }

  pauseConversation(conversationId) {
    const conversation = this.conversations.get(conversationId);
    if (conversation) {
      conversation.state = this.conversationStates.PAUSED;
      conversation.pauseTime = new Date().toISOString();

      this.emit('conversationPaused', {
        conversationId,
        timestamp: new Date().toISOString()
      });
    }
  }

  resumeConversation(conversationId) {
    const conversation = this.conversations.get(conversationId);
    if (conversation && conversation.state === this.conversationStates.PAUSED) {
      conversation.state = this.conversationStates.RESUMING;
      conversation.resumeTime = new Date().toISOString();

      // Rebuild context
      setTimeout(async () => {
        const context = await this.buildContextualAwareness(conversationId);
        conversation.state = this.conversationStates.ACTIVE;

        this.emit('conversationResumed', {
          conversationId,
          context,
          timestamp: new Date().toISOString()
        });
      }, 100);
    }
  }

  concludeConversation(conversationId) {
    const conversation = this.conversations.get(conversationId);
    if (conversation) {
      conversation.state = this.conversationStates.CONCLUDING;
      conversation.endTime = new Date().toISOString();

      // Move to long-term memory
      this.archiveConversation(conversation);

      conversation.state = this.conversationStates.CONCLUDED;

      this.emit('conversationConcluded', {
        conversationId,
        duration: this.calculateConversationDuration(conversation),
        summary: this.generateConversationSummary(conversation),
        timestamp: new Date().toISOString()
      });
    }
  }

  archiveConversation(conversation) {
    // Store conversation in long-term memory
    conversation.participants.forEach(participant => {
      if (!this.longTermMemory.has(participant.id)) {
        this.longTermMemory.set(participant.id, []);
      }

      const memory = this.longTermMemory.get(participant.id);
      memory.push({
        type: 'conversation',
        conversationId: conversation.id,
        summary: this.generateConversationSummary(conversation),
        timestamp: conversation.endTime,
        duration: this.calculateConversationDuration(conversation),
        participants: conversation.participants.map(p => p.id),
        topics: conversation.metadata.topics,
        emotionalTrajectory: conversation.metadata.emotionalTrajectory
      });

      // Limit memory size
      if (memory.length > this.options.longTermMemoryLimit) {
        memory.shift();
      }
    });
  }

  generateConversationSummary(conversation) {
    return {
      duration: this.calculateConversationDuration(conversation),
      participants: conversation.participants.length,
      messages: conversation.messages.length,
      topics: conversation.metadata.topics,
      keyMoments: conversation.metadata.keyMoments.length,
      emotionalPeak: this.findEmotionalPeak(conversation)
    };
  }

  findEmotionalPeak(conversation) {
    // This would analyze emotional trajectory to find peak moments
    return {
      timestamp: conversation.messages[Math.floor(conversation.messages.length / 2)]?.timestamp,
      emotion: 'neutral',
      intensity: 0.5
    };
  }

  // API Methods
  getConversation(conversationId) {
    return this.conversations.get(conversationId);
  }

  getActiveConversations() {
    return Array.from(this.conversations.values())
      .filter(conv => conv.state === this.conversationStates.ACTIVE);
  }

  getSpeakerMemory(speakerId, type = 'short') {
    return type === 'short'
      ? this.shortTermMemory.get(speakerId) || []
      : this.longTermMemory.get(speakerId) || [];
  }

  getRelationships(speakerId) {
    const relationships = {};

    for (const [key, relationship] of this.relationshipContext) {
      if (key.startsWith(`${speakerId}-`)) {
        const otherId = key.split('-')[1];
        relationships[otherId] = relationship;
      }
    }

    return relationships;
  }

  getWorldEvents() {
    return Array.from(this.worldEvents.values());
  }

  reset() {
    this.conversations.clear();
    this.shortTermMemory.clear();
    this.longTermMemory.clear();
    this.environmentalContext.clear();
    this.relationshipContext.clear();
    this.campaignKnowledge.clear();
    this.worldEvents.clear();
  }
}

module.exports = ContextAwareConversationManager;