const EventEmitter = require('events');
const moment = require('moment');
const _ = require('lodash');

class ConversationAnalyticsEngine extends EventEmitter {
  constructor(options = {}) {
    super();

    // Analytics data stores
    this.conversationMetrics = new Map();
    this.playerEngagement = new Map();
    this.satisfactionScores = new Map();
    this.dialogueEffectiveness = new Map();
    this.emotionalTrends = new Map();
    this.relationshipMetrics = new Map();
    this.topicAnalysis = new Map();
    this.performanceMetrics = new Map();

    // Real-time analytics
    this.realTimeMetrics = {
      activeConversations: 0,
      totalMessages: 0,
      averageResponseTime: 0,
      sentimentDistribution: {},
      emotionDistribution: {},
      topicPopularity: {},
      playerActivity: {}
    };

    // Historical analytics
    this.historicalData = {
      daily: new Map(),
      weekly: new Map(),
      monthly: new Map(),
      yearly: new Map()
    };

    // Configuration
    this.options = {
      dataRetentionDays: options.dataRetentionDays || 365,
      aggregationInterval: options.aggregationInterval || 60000, // 1 minute
      enableRealTimeAnalysis: options.enableRealTimeAnalysis !== false,
      enablePredictiveAnalytics: options.enablePredictiveAnalytics !== false,
      enableTrendAnalysis: options.enableTrendAnalysis !== false,
      enableSentimentAnalysis: options.enableSentimentAnalysis !== false,
      batchSize: options.batchSize || 100,
      ...options
    };

    // Analytics processors
    this.processors = {
      sentiment: new SentimentAnalyzer(),
      emotion: new EmotionAnalyzer(),
      topic: new TopicAnalyzer(),
      engagement: new EngagementAnalyzer(),
      effectiveness: new EffectivenessAnalyzer(),
      relationship: new RelationshipAnalyzer(),
      satisfaction: new SatisfactionAnalyzer()
    };

    // Start aggregation and cleanup
    this.startAggregation();
    this.startDataCleanup();
  }

  async trackConversation(conversationId, conversationData) {
    try {
      const metrics = await this.analyzeConversation(conversationData);

      // Store conversation metrics
      this.conversationMetrics.set(conversationId, {
        ...metrics,
        conversationId,
        timestamp: new Date().toISOString(),
        lastUpdated: new Date().toISOString()
      });

      // Update real-time metrics
      this.updateRealTimeMetrics(conversationData, metrics);

      // Process player engagement
      await this.processPlayerEngagement(conversationId, conversationData);

      // Process dialogue effectiveness
      await this.processDialogueEffectiveness(conversationId, conversationData);

      // Track emotional trends
      this.trackEmotionalTrends(conversationId, conversationData);

      // Analyze topics
      this.analyzeTopics(conversationId, conversationData);

      // Update relationship metrics
      this.updateRelationshipMetrics(conversationId, conversationData);

      this.emit('conversationTracked', {
        conversationId,
        metrics,
        timestamp: new Date().toISOString()
      });

      return metrics;

    } catch (error) {
      console.error('Error tracking conversation:', error);
      throw new Error(`Conversation tracking failed: ${error.message}`);
    }
  }

  async analyzeConversation(conversationData) {
    const analysis = {
      basic: this.analyzeBasicMetrics(conversationData),
      sentiment: this.analyzeSentimentMetrics(conversationData),
      emotional: this.analyzeEmotionalMetrics(conversationData),
      engagement: await this.analyzeEngagementMetrics(conversationData),
      effectiveness: await this.analyzeEffectivenessMetrics(conversationData),
      topic: this.analyzeTopicMetrics(conversationData),
      temporal: this.analyzeTemporalMetrics(conversationData),
      quality: this.analyzeQualityMetrics(conversationData)
    };

    // Calculate overall scores
    analysis.overall = this.calculateOverallScores(analysis);

    return analysis;
  }

  analyzeBasicMetrics(conversationData) {
    const messages = conversationData.messages || [];
    const participants = conversationData.participants || [];

    return {
      messageCount: messages.length,
      participantCount: participants.length,
      averageMessagesPerParticipant: participants.length > 0 ? messages.length / participants.length : 0,
      averageMessageLength: this.calculateAverageMessageLength(messages),
      totalDuration: this.calculateConversationDuration(conversationData),
      averageResponseTime: this.calculateAverageResponseTime(messages),
      conversationTurns: this.calculateConversationTurns(messages)
    };
  }

  calculateAverageMessageLength(messages) {
    if (messages.length === 0) return 0;

    const totalLength = messages.reduce((sum, message) => {
      return sum + (message.content ? message.content.length : 0);
    }, 0);

    return totalLength / messages.length;
  }

  calculateConversationDuration(conversationData) {
    if (!conversationData.startTime) return 0;

    const startTime = moment(conversationData.startTime);
    const endTime = conversationData.endTime ? moment(conversationData.endTime) : moment();

    return endTime.diff(startTime, 'seconds');
  }

  calculateAverageResponseTime(messages) {
    if (messages.length < 2) return 0;

    const responseTimes = [];
    for (let i = 1; i < messages.length; i++) {
      const currentMessage = messages[i];
      const previousMessage = messages[i - 1];

      if (currentMessage.speakerId !== previousMessage.speakerId) {
        const responseTime = moment(currentMessage.timestamp).diff(moment(previousMessage.timestamp), 'milliseconds');
        responseTimes.push(responseTime);
      }
    }

    return responseTimes.length > 0 ? responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length : 0;
  }

  calculateConversationTurns(messages) {
    let turns = 0;
    let lastSpeaker = null;

    for (const message of messages) {
      if (message.speakerId !== lastSpeaker) {
        turns++;
        lastSpeaker = message.speakerId;
      }
    }

    return turns;
  }

  analyzeSentimentMetrics(conversationData) {
    const messages = conversationData.messages || [];
    const sentiments = messages.map(message => this.processors.sentiment.analyze(message.content || ''));

    return {
      overallSentiment: this.calculateOverallSentiment(sentiments),
      sentimentDistribution: this.calculateSentimentDistribution(sentiments),
      sentimentProgression: this.calculateSentimentProgression(sentiments),
      sentimentVolatility: this.calculateSentimentVolatility(sentiments),
      positiveMessageRatio: this.calculatePositiveRatio(sentiments),
      sentimentIntensity: this.calculateSentimentIntensity(sentiments)
    };
  }

  calculateOverallSentiment(sentiments) {
    if (sentiments.length === 0) return 0;

    const totalScore = sentiments.reduce((sum, sentiment) => sum + sentiment.score, 0);
    return totalScore / sentiments.length;
  }

  calculateSentimentDistribution(sentiments) {
    const distribution = { positive: 0, negative: 0, neutral: 0 };

    sentiments.forEach(sentiment => {
      if (sentiment.score > 0.1) distribution.positive++;
      else if (sentiment.score < -0.1) distribution.negative++;
      else distribution.neutral++;
    });

    return {
      ...distribution,
      percentages: {
        positive: (distribution.positive / sentiments.length) * 100,
        negative: (distribution.negative / sentiments.length) * 100,
        neutral: (distribution.neutral / sentiments.length) * 100
      }
    };
  }

  calculateSentimentProgression(sentiments) {
    if (sentiments.length < 2) return { trend: 'stable', change: 0 };

    const firstHalf = sentiments.slice(0, Math.floor(sentiments.length / 2));
    const secondHalf = sentiments.slice(Math.floor(sentiments.length / 2));

    const firstAvg = this.calculateOverallSentiment(firstHalf);
    const secondAvg = this.calculateOverallSentiment(secondHalf);

    const change = secondAvg - firstAvg;
    let trend = 'stable';

    if (change > 0.2) trend = 'improving';
    else if (change < -0.2) trend = 'declining';
    else if (change > 0) trend = 'slightly_improving';
    else if (change < 0) trend = 'slightly_declining';

    return { trend, change, firstAvg, secondAvg };
  }

  calculateSentimentVolatility(sentiments) {
    if (sentiments.length < 2) return 0;

    const scores = sentiments.map(s => s.score);
    const mean = scores.reduce((sum, score) => sum + score, 0) / scores.length;
    const variance = scores.reduce((sum, score) => sum + Math.pow(score - mean, 2), 0) / scores.length;

    return Math.sqrt(variance);
  }

  calculatePositiveRatio(sentiments) {
    const positiveCount = sentiments.filter(s => s.score > 0.1).length;
    return sentiments.length > 0 ? positiveCount / sentiments.length : 0;
  }

  calculateSentimentIntensity(sentiments) {
    const intensities = sentiments.map(s => Math.abs(s.score));
    return intensities.reduce((sum, intensity) => sum + intensity, 0) / intensities.length;
  }

  analyzeEmotionalMetrics(conversationData) {
    const messages = conversationData.messages || [];
    const emotions = messages.map(message =>
      this.processors.emotion.analyze(message.content, message.emotionalState)
    );

    return {
      primaryEmotions: this.identifyPrimaryEmotions(emotions),
      emotionalDiversity: this.calculateEmotionalDiversity(emotions),
      emotionalIntensity: this.calculateEmotionalIntensity(emotions),
      emotionalProgression: this.calculateEmotionalProgression(emotions),
      emotionalTriggers: this.identifyEmotionalTriggers(emotions, messages),
      empathyIndicators: this.identifyEmpathyIndicators(emotions, messages)
    };
  }

  identifyPrimaryEmotions(emotions) {
    const emotionCounts = {};
    const emotionIntensities = {};

    emotions.forEach(emotionData => {
      Object.entries(emotionData.emotions).forEach(([emotion, intensity]) => {
        emotionCounts[emotion] = (emotionCounts[emotion] || 0) + (intensity > 0.5 ? 1 : 0);
        emotionIntensities[emotion] = (emotionIntensities[emotion] || []).push(intensity);
      });
    });

    const primaryEmotions = Object.entries(emotionCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([emotion, count]) => ({
        emotion,
        frequency: count,
        averageIntensity: emotionIntensities[emotion].reduce((sum, i) => sum + i, 0) / emotionIntensities[emotion].length
      }));

    return primaryEmotions;
  }

  calculateEmotionalDiversity(emotions) {
    const uniqueEmotions = new Set();

    emotions.forEach(emotionData => {
      Object.keys(emotionData.emotions).forEach(emotion => {
        if (emotionData.emotions[emotion] > 0.3) {
          uniqueEmotions.add(emotion);
        }
      });
    });

    return uniqueEmotions.size;
  }

  calculateEmotionalIntensity(emotions) {
    const allIntensities = emotions.flatMap(e => Object.values(e.emotions));
    return allIntensities.reduce((sum, intensity) => sum + intensity, 0) / allIntensities.length;
  }

  calculateEmotionalProgression(emotions) {
    if (emotions.length < 2) return { trend: 'stable', dominantEmotion: 'neutral' };

    const segments = this.segmentEmotions(emotions);
    const progression = segments.map(segment => this.identifyDominantEmotion(segment));

    const trend = this.analyzeEmotionalTrend(progression);
    const dominantEmotion = this.getMostFrequentEmotion(progression);

    return { trend, dominantEmotion, progression };
  }

  segmentEmotions(emotions, segmentSize = 5) {
    const segments = [];
    for (let i = 0; i < emotions.length; i += segmentSize) {
      segments.push(emotions.slice(i, i + segmentSize));
    }
    return segments;
  }

  identifyDominantEmotion(emotionSegment) {
    const emotionSums = {};

    emotionSegment.forEach(emotionData => {
      Object.entries(emotionData.emotions).forEach(([emotion, intensity]) => {
        emotionSums[emotion] = (emotionSums[emotion] || 0) + intensity;
      });
    });

    return Object.entries(emotionSums)
      .sort((a, b) => b[1] - a[1])[0]?.[0] || 'neutral';
  }

  analyzeEmotionalTrend(progression) {
    if (progression.length < 3) return 'stable';

    const transitions = progression.slice(1).map((emotion, index) => ({
      from: progression[index],
      to: emotion
    }));

    const positiveTransitions = transitions.filter(t =>
      this.isPositiveTransition(t.from, t.to)
    ).length;

    const negativeTransitions = transitions.filter(t =>
      this.isNegativeTransition(t.from, t.to)
    ).length;

    if (positiveTransitions > negativeTransitions * 1.5) return 'improving';
    if (negativeTransitions > positiveTransitions * 1.5) return 'declining';
    return 'fluctuating';
  }

  isPositiveTransition(from, to) {
    const positiveEmotions = ['happiness', 'excitement', 'trust', 'anticipation'];
    const negativeEmotions = ['sadness', 'anger', 'fear', 'disgust'];

    return negativeEmotions.includes(from) && positiveEmotions.includes(to);
  }

  isNegativeTransition(from, to) {
    const positiveEmotions = ['happiness', 'excitement', 'trust', 'anticipation'];
    const negativeEmotions = ['sadness', 'anger', 'fear', 'disgust'];

    return positiveEmotions.includes(from) && negativeEmotions.includes(to);
  }

  getMostFrequentEmotion(emotions) {
    const frequency = {};
    emotions.forEach(emotion => {
      frequency[emotion] = (frequency[emotion] || 0) + 1;
    });

    return Object.entries(frequency)
      .sort((a, b) => b[1] - a[1])[0]?.[0] || 'neutral';
  }

  identifyEmotionalTriggers(emotions, messages) {
    const triggers = {};

    emotions.forEach((emotionData, index) => {
      const message = messages[index];
      if (!message || !message.content) return;

      Object.entries(emotionData.emotions).forEach(([emotion, intensity]) => {
        if (intensity > 0.7) {
          const words = message.content.toLowerCase().split(/\s+/);
          words.forEach(word => {
            if (word.length > 3) { // Filter out very short words
              if (!triggers[word]) triggers[word] = {};
              triggers[word][emotion] = (triggers[word][emotion] || 0) + intensity;
            }
          });
        }
      });
    });

    // Filter and rank triggers
    const rankedTriggers = Object.entries(triggers)
      .filter(([word, emotions]) => Object.values(emotions).reduce((sum, i) => sum + i, 0) > 1.0)
      .map(([word, emotions]) => ({
        word,
        emotions,
        totalIntensity: Object.values(emotions).reduce((sum, i) => sum + i, 0)
      }))
      .sort((a, b) => b.totalIntensity - a.totalIntensity)
      .slice(0, 10);

    return rankedTriggers;
  }

  identifyEmpathyIndicators(emotions, messages) {
    const empathyPhrases = [
      'i understand', 'that must be', 'i can see', 'you must feel',
      'it sounds like', 'that sounds', 'i hear', 'i appreciate'
    ];

    let empathyCount = 0;
    let empatheticResponses = [];

    messages.forEach((message, index) => {
      if (!message || !message.content) return;

      const content = message.content.toLowerCase();
      const hasEmpathyPhrase = empathyPhrases.some(phrase => content.includes(phrase));

      if (hasEmpathyPhrase) {
        empathyCount++;
        empatheticResponses.push({
          index,
          content: message.content,
          emotionalContext: emotions[index]?.emotions || {}
        });
      }
    });

    return {
      count: empathyCount,
      ratio: messages.length > 0 ? empathyCount / messages.length : 0,
      responses: empatheticResponses.slice(0, 5) // Return top 5 examples
    };
  }

  async analyzeEngagementMetrics(conversationData) {
    return await this.processors.engagement.analyze(conversationData);
  }

  async analyzeEffectivenessMetrics(conversationData) {
    return await this.processors.effectiveness.analyze(conversationData);
  }

  analyzeTopicMetrics(conversationData) {
    const messages = conversationData.messages || [];
    const topics = this.processors.topic.extractTopics(messages);

    return {
      primaryTopics: this.identifyPrimaryTopics(topics),
      topicDiversity: this.calculateTopicDiversity(topics),
      topicProgression: this.analyzeTopicProgression(topics),
      topicEngagement: this.calculateTopicEngagement(topics, messages)
    };
  }

  identifyPrimaryTopics(topics) {
    const topicCounts = {};
    topics.forEach(topic => {
      topicCounts[topic] = (topicCounts[topic] || 0) + 1;
    });

    return Object.entries(topicCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([topic, count]) => ({ topic, frequency: count }));
  }

  calculateTopicDiversity(topics) {
    const uniqueTopics = new Set(topics);
    return topics.length > 0 ? uniqueTopics.size / topics.length : 0;
  }

  analyzeTopicProgression(topics) {
    if (topics.length < 2) return { trend: 'stable', transitions: [] };

    const segments = this.segmentTopics(topics);
    const dominantTopics = segments.map(segment => this.getMostFrequentTopic(segment));

    const transitions = dominantTopics.slice(1).map((topic, index) => ({
      from: dominantTopics[index],
      to: topic,
      position: index
    }));

    return {
      trend: this.analyzeTopicTrend(dominantTopics),
      transitions: transitions.slice(0, 10),
      dominantTopics
    };
  }

  segmentTopics(topics, segmentSize = 3) {
    const segments = [];
    for (let i = 0; i < topics.length; i += segmentSize) {
      segments.push(topics.slice(i, i + segmentSize));
    }
    return segments;
  }

  getMostFrequentTopic(topics) {
    const frequency = {};
    topics.forEach(topic => {
      frequency[topic] = (frequency[topic] || 0) + 1;
    });

    return Object.entries(frequency)
      .sort((a, b) => b[1] - a[1])[0]?.[0] || 'general';
  }

  analyzeTopicTrend(dominantTopics) {
    const uniqueTopics = new Set(dominantTopics);

    if (uniqueTopics.size === 1) return 'focused';
    if (uniqueTopics.size > dominantTopics.length * 0.7) return 'scattered';
    return 'exploratory';
  }

  calculateTopicEngagement(topics, messages) {
    const engagementByTopic = {};

    topics.forEach((topic, index) => {
      if (!engagementByTopic[topic]) {
        engagementByTopic[topic] = {
          messageCount: 0,
          averageLength: 0,
          responses: 0
        };
      }

      const message = messages[index];
      if (message) {
        engagementByTopic[topic].messageCount++;
        engagementByTopic[topic].averageLength += (message.content || '').length;

        // Count responses to this message
        if (index < messages.length - 1) {
          const nextMessage = messages[index + 1];
          if (nextMessage.speakerId !== message.speakerId) {
            engagementByTopic[topic].responses++;
          }
        }
      }
    });

    // Calculate averages
    Object.values(engagementByTopic).forEach(engagement => {
      engagement.averageLength = engagement.messageCount > 0 ?
        engagement.averageLength / engagement.messageCount : 0;
      engagement.responseRate = engagement.messageCount > 0 ?
        engagement.responses / engagement.messageCount : 0;
    });

    return engagementByTopic;
  }

  analyzeTemporalMetrics(conversationData) {
    const messages = conversationData.messages || [];
    const startTime = conversationData.startTime ? moment(conversationData.startTime) : moment();

    return {
      timeOfDay: startTime.format('HH:mm'),
      dayOfWeek: startTime.format('dddd'),
      duration: this.calculateConversationDuration(conversationData),
      messageFrequency: this.calculateMessageFrequency(messages),
      activePeriods: this.identifyActivePeriods(messages),
      pauses: this.analyzePauses(messages),
      conversationPacing: this.analyzeConversationPacing(messages)
    };
  }

  calculateMessageFrequency(messages) {
    if (messages.length < 2) return 0;

    const startTime = moment(messages[0].timestamp);
    const endTime = moment(messages[messages.length - 1].timestamp);
    const duration = endTime.diff(startTime, 'minutes');

    return duration > 0 ? messages.length / duration : 0;
  }

  identifyActivePeriods(messages) {
    const periods = [];
    const windowSize = 5; // 5 messages per period

    for (let i = 0; i < messages.length; i += windowSize) {
      const window = messages.slice(i, i + windowSize);
      if (window.length >= 2) {
        const periodDuration = moment(window[window.length - 1].timestamp)
          .diff(moment(window[0].timestamp), 'seconds');

        periods.push({
          start: i,
          end: Math.min(i + windowSize, messages.length),
          duration: periodDuration,
          messageCount: window.length,
          frequency: periodDuration > 0 ? window.length / periodDuration * 60 : 0 // messages per minute
        });
      }
    }

    return periods;
  }

  analyzePauses(messages) {
    const pauses = [];
    const threshold = 30000; // 30 seconds

    for (let i = 1; i < messages.length; i++) {
      const currentMessage = messages[i];
      const previousMessage = messages[i - 1];

      const pauseDuration = moment(currentMessage.timestamp)
        .diff(moment(previousMessage.timestamp), 'milliseconds');

      if (pauseDuration > threshold) {
        pauses.push({
          position: i,
          duration: pauseDuration,
          afterMessage: previousMessage.speakerId,
          beforeMessage: currentMessage.speakerId
        });
      }
    }

    return {
      count: pauses.length,
      averageDuration: pauses.length > 0 ?
        pauses.reduce((sum, p) => sum + p.duration, 0) / pauses.length : 0,
      longestPause: pauses.length > 0 ? Math.max(...pauses.map(p => p.duration)) : 0,
      pauses: pauses.slice(0, 5) // Return top 5 longest pauses
    };
  }

  analyzeConversationPacing(messages) {
    if (messages.length < 2) return { rhythm: 'unknown', variance: 0 };

    const responseTimes = [];
    for (let i = 1; i < messages.length; i++) {
      const currentMessage = messages[i];
      const previousMessage = messages[i - 1];

      if (currentMessage.speakerId !== previousMessage.speakerId) {
        const responseTime = moment(currentMessage.timestamp)
          .diff(moment(previousMessage.timestamp), 'milliseconds');
        responseTimes.push(responseTime);
      }
    }

    if (responseTimes.length === 0) return { rhythm: 'monologue', variance: 0 };

    const avgResponseTime = responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length;
    const variance = responseTimes.reduce((sum, time) => sum + Math.pow(time - avgResponseTime, 2), 0) / responseTimes.length;
    const stdDev = Math.sqrt(variance);

    let rhythm = 'steady';
    if (stdDev > avgResponseTime * 0.5) rhythm = 'variable';
    if (avgResponseTime < 5000) rhythm = 'rapid';
    if (avgResponseTime > 30000) rhythm = 'slow';

    return {
      rhythm,
      averageResponseTime: avgResponseTime,
      variance,
      standardDeviation: stdDev,
      responseCount: responseTimes.length
    };
  }

  analyzeQualityMetrics(conversationData) {
    const messages = conversationData.messages || [];

    return {
      coherence: this.calculateCoherence(messages),
      relevance: this.calculateRelevance(messages),
      clarity: this.calculateClarity(messages),
      depth: this.calculateDepth(messages),
      constructiveness: this.calculateConstructiveness(messages),
      resolution: this.calculateResolution(conversationData)
    };
  }

  calculateCoherence(messages) {
    // Simple coherence analysis based on topic continuity
    if (messages.length < 2) return 1.0;

    let coherenceScore = 0;
    let coherenceCount = 0;

    for (let i = 1; i < messages.length; i++) {
      const currentTopics = this.processors.topic.extractTopics([messages[i]]);
      const previousTopics = this.processors.topic.extractTopics([messages[i - 1]]);

      const commonTopics = currentTopics.filter(topic => previousTopics.includes(topic));
      const coherence = commonTopics.length / Math.max(currentTopics.length, 1);

      coherenceScore += coherence;
      coherenceCount++;
    }

    return coherenceCount > 0 ? coherenceScore / coherenceCount : 0.5;
  }

  calculateRelevance(messages) {
    // Relevance based on conversation context and goals
    return 0.8; // Placeholder - would need context analysis
  }

  calculateClarity(messages) {
    // Clarity based on message complexity and readability
    let totalClarity = 0;
    let messageCount = 0;

    messages.forEach(message => {
      if (message.content) {
        const words = message.content.split(/\s+/);
        const sentences = message.content.split(/[.!?]+/).length;
        const avgWordsPerSentence = words.length / sentences;

        // Optimal is 10-20 words per sentence
        const clarity = Math.max(0, 1 - Math.abs(avgWordsPerSentence - 15) / 15);
        totalClarity += clarity;
        messageCount++;
      }
    });

    return messageCount > 0 ? totalClarity / messageCount : 0.5;
  }

  calculateDepth(messages) {
    // Depth based on complexity and substance of content
    const depthIndicators = ['why', 'how', 'because', 'therefore', 'however', 'although'];
    let depthScore = 0;
    let totalWords = 0;

    messages.forEach(message => {
      if (message.content) {
        const words = message.content.toLowerCase().split(/\s+/);
        totalWords += words.length;

        const depthWords = words.filter(word => depthIndicators.includes(word));
        depthScore += depthWords.length;
      }
    });

    return totalWords > 0 ? Math.min(1.0, depthScore / (totalWords * 0.1)) : 0.3;
  }

  calculateConstructiveness(messages) {
    // Constructiveness based on positive contribution indicators
    const constructiveIndicators = [
      'let\'s', 'we can', 'how about', 'perhaps', 'maybe', 'suggest',
      'recommend', 'advise', 'propose', 'offer', 'help'
    ];

    let constructiveCount = 0;
    let totalMessages = 0;

    messages.forEach(message => {
      if (message.content) {
        totalMessages++;
        const content = message.content.toLowerCase();
        const hasConstructive = constructiveIndicators.some(indicator => content.includes(indicator));
        if (hasConstructive) constructiveCount++;
      }
    });

    return totalMessages > 0 ? constructiveCount / totalMessages : 0.3;
  }

  calculateResolution(conversationData) {
    // Resolution based on whether conversation achieved its goals
    // This would need access to conversation objectives
    return 0.7; // Placeholder
  }

  calculateOverallScores(analysis) {
    return {
      conversationQuality: this.calculateWeightedScore([
        { metric: analysis.basic.messageCount, weight: 0.1, normalize: { max: 50, ideal: 20 } },
        { metric: analysis.sentiment.overallSentiment, weight: 0.2, normalize: { min: -1, max: 1, ideal: 0.3 } },
        { metric: analysis.engagement?.score || 0.5, weight: 0.3 },
        { metric: analysis.effectiveness?.score || 0.5, weight: 0.25 },
        { metric: analysis.quality.coherence, weight: 0.15 }
      ]),
      playerEngagement: analysis.engagement?.score || 0.5,
      dialogueEffectiveness: analysis.effectiveness?.score || 0.5,
      emotionalIntelligence: this.calculateEmotionalIntelligenceScore(analysis.emotional),
      topicRelevance: this.calculateTopicRelevanceScore(analysis.topic),
      overallSatisfaction: this.calculateSatisfactionScore(analysis)
    };
  }

  calculateWeightedScore(components) {
    let totalScore = 0;
    let totalWeight = 0;

    components.forEach(component => {
      let normalizedValue = component.metric;

      if (component.normalize) {
        const { min = 0, max = 1, ideal } = component.normalize;

        if (ideal !== undefined) {
          // Score based on distance from ideal
          const distance = Math.abs(component.metric - ideal);
          const maxDistance = Math.max(ideal - min, max - ideal);
          normalizedValue = Math.max(0, 1 - distance / maxDistance);
        } else {
          // Simple normalization
          normalizedValue = (component.metric - min) / (max - min);
        }
      }

      totalScore += normalizedValue * component.weight;
      totalWeight += component.weight;
    });

    return totalWeight > 0 ? totalScore / totalWeight : 0;
  }

  calculateEmotionalIntelligenceScore(emotionalAnalysis) {
    const components = [
      { metric: emotionalAnalysis.emotionalDiversity / 8, weight: 0.2 }, // Normalize by max emotions
      { metric: emotionalAnalysis.emotionalIntensity, weight: 0.15 },
      { metric: emotionalAnalysis.empathyIndicators.ratio, weight: 0.35 },
      { metric: emotionalAnalysis.primaryEmotions?.length || 0, weight: 0.15, normalize: { max: 5 } },
      { metric: emotionalAnalysis.emotionalProgression.trend === 'improving' ? 1 : 0.5, weight: 0.15 }
    ];

    return this.calculateWeightedScore(components);
  }

  calculateTopicRelevanceScore(topicAnalysis) {
    const components = [
      { metric: topicAnalysis.topicDiversity, weight: 0.3 },
      { metric: topicAnalysis.primaryTopics?.length || 0, weight: 0.2, normalize: { max: 10 } },
      { metric: Object.values(topicAnalysis.topicEngagement || {}).reduce((sum, e) => sum + e.responseRate, 0) /
               Math.max(Object.keys(topicAnalysis.topicEngagement || {}).length, 1), weight: 0.5 }
    ];

    return this.calculateWeightedScore(components);
  }

  calculateSatisfactionScore(analysis) {
    const components = [
      { metric: analysis.sentiment.overallSentiment, weight: 0.3, normalize: { min: -1, max: 1 } },
      { metric: analysis.quality.coherence, weight: 0.2 },
      { metric: analysis.quality.constructiveness, weight: 0.2 },
      { metric: analysis.engagement?.score || 0.5, weight: 0.3 }
    ];

    return this.calculateWeightedScore(components);
  }

  updateRealTimeMetrics(conversationData, metrics) {
    // Update active conversations
    this.realTimeMetrics.activeConversations++;

    // Update total messages
    this.realTimeMetrics.totalMessages += conversationData.messages?.length || 0;

    // Update average response time
    const newResponseTime = metrics.basic.averageResponseTime;
    const currentAvg = this.realTimeMetrics.averageResponseTime;
    const count = this.realTimeMetrics.activeConversations;
    this.realTimeMetrics.averageResponseTime = (currentAvg * (count - 1) + newResponseTime) / count;

    // Update sentiment distribution
    const sentiment = metrics.sentiment;
    this.realTimeMetrics.sentimentDistribution = {
      positive: (this.realTimeMetrics.sentimentDistribution.positive || 0) + sentiment.sentimentDistribution.percentages.positive / 100,
      negative: (this.realTimeMetrics.sentimentDistribution.negative || 0) + sentiment.sentimentDistribution.percentages.negative / 100,
      neutral: (this.realTimeMetrics.sentimentDistribution.neutral || 0) + sentiment.sentimentDistribution.percentages.neutral / 100
    };

    // Update emotion distribution
    metrics.emotional.primaryEmotions?.forEach(({ emotion, frequency }) => {
      this.realTimeMetrics.emotionDistribution[emotion] =
        (this.realTimeMetrics.emotionDistribution[emotion] || 0) + frequency;
    });

    // Update topic popularity
    metrics.topic.primaryTopics?.forEach(({ topic, frequency }) => {
      this.realTimeMetrics.topicPopularity[topic] =
        (this.realTimeMetrics.topicPopularity[topic] || 0) + frequency;
    });

    this.emit('realTimeMetricsUpdated', this.realTimeMetrics);
  }

  async processPlayerEngagement(conversationId, conversationData) {
    const engagement = await this.processors.engagement.calculateEngagement(conversationData);
    this.playerEngagement.set(conversationId, {
      ...engagement,
      conversationId,
      timestamp: new Date().toISOString()
    });
  }

  async processDialogueEffectiveness(conversationId, conversationData) {
    const effectiveness = await this.processors.effectiveness.calculateEffectiveness(conversationData);
    this.dialogueEffectiveness.set(conversationId, {
      ...effectiveness,
      conversationId,
      timestamp: new Date().toISOString()
    });
  }

  trackEmotionalTrends(conversationId, conversationData) {
    const emotionalData = conversationData.messages?.map(message => ({
      timestamp: message.timestamp,
      emotions: message.emotionalState || {}
    })) || [];

    this.emotionalTrends.set(conversationId, {
      data: emotionalData,
      conversationId,
      timestamp: new Date().toISOString()
    });
  }

  analyzeTopics(conversationId, conversationData) {
    const topics = this.processors.topic.extractTopics(conversationData.messages || []);
    this.topicAnalysis.set(conversationId, {
      topics,
      conversationId,
      timestamp: new Date().toISOString()
    });
  }

  updateRelationshipMetrics(conversationId, conversationData) {
    const participants = conversationData.participants || [];
    const relationships = {};

    participants.forEach(participant => {
      participants.forEach(otherParticipant => {
        if (participant.id !== otherParticipant.id) {
          const relationshipKey = `${participant.id}-${otherParticipant.id}`;
          relationships[relationshipKey] = this.calculateRelationshipScore(participant, otherParticipant, conversationData);
        }
      });
    });

    this.relationshipMetrics.set(conversationId, {
      relationships,
      conversationId,
      timestamp: new Date().toISOString()
    });
  }

  calculateRelationshipScore(participant1, participant2, conversationData) {
    // Calculate relationship strength based on interaction patterns
    const messages = conversationData.messages || [];
    const interactions = messages.filter(message =>
      (message.speakerId === participant1.id || message.speakerId === participant2.id) &&
      messages.some(m =>
        m !== message &&
        (m.speakerId === participant1.id || m.speakerId === participant2.id) &&
        Math.abs(new Date(m.timestamp) - new Date(message.timestamp)) < 300000 // Within 5 minutes
      )
    );

    return {
      interactionCount: interactions.length,
      responseRate: this.calculateResponseRate(participant1.id, participant2.id, messages),
      sentimentScore: this.calculateInteractionSentiment(participant1.id, participant2.id, messages),
      topicAlignment: this.calculateTopicAlignment(participant1.id, participant2.id, messages)
    };
  }

  calculateResponseRate(speaker1Id, speaker2Id, messages) {
    let responses = 0;
    let opportunities = 0;

    for (let i = 0; i < messages.length - 1; i++) {
      const currentMessage = messages[i];
      const nextMessage = messages[i + 1];

      if (currentMessage.speakerId === speaker1Id && nextMessage.speakerId === speaker2Id) {
        responses++;
        opportunities++;
      } else if (currentMessage.speakerId === speaker1Id) {
        opportunities++;
      }
    }

    return opportunities > 0 ? responses / opportunities : 0;
  }

  calculateInteractionSentiment(speaker1Id, speaker2Id, messages) {
    const interactionMessages = messages.filter(message =>
      message.speakerId === speaker1Id || message.speakerId === speaker2Id
    );

    const sentiments = interactionMessages.map(message =>
      this.processors.sentiment.analyze(message.content || '')
    );

    const avgSentiment = sentiments.reduce((sum, sentiment) => sum + sentiment.score, 0) / sentiments.length;
    return avgSentiment;
  }

  calculateTopicAlignment(speaker1Id, speaker2Id, messages) {
    const speaker1Messages = messages.filter(m => m.speakerId === speaker1Id);
    const speaker2Messages = messages.filter(m => m.speakerId === speaker2Id);

    const speaker1Topics = this.processors.topic.extractTopics(speaker1Messages);
    const speaker2Topics = this.processors.topic.extractTopics(speaker2Messages);

    const commonTopics = speaker1Topics.filter(topic => speaker2Topics.includes(topic));
    const totalTopics = new Set([...speaker1Topics, ...speaker2Topics]).size;

    return totalTopics > 0 ? commonTopics.length / totalTopics : 0;
  }

  startAggregation() {
    setInterval(() => {
      this.aggregateMetrics();
    }, this.options.aggregationInterval);
  }

  aggregateMetrics() {
    const now = moment();
    const dailyKey = now.format('YYYY-MM-DD');
    const weeklyKey = now.format('YYYY-[W]WW');
    const monthlyKey = now.format('YYYY-MM');
    const yearlyKey = now.format('YYYY');

    // Aggregate historical data
    this.aggregateToPeriod('daily', dailyKey);
    this.aggregateToPeriod('weekly', weeklyKey);
    this.aggregateToPeriod('monthly', monthlyKey);
    this.aggregateToPeriod('yearly', yearlyKey);

    this.emit('metricsAggregated', {
      timestamp: new Date().toISOString(),
      periods: { daily: dailyKey, weekly: weeklyKey, monthly: monthlyKey, yearly: yearlyKey }
    });
  }

  aggregateToPeriod(period, key) {
    if (!this.historicalData[period].has(key)) {
      this.historicalData[period].set(key, {
        conversationCount: 0,
        totalMessages: 0,
        averageSentiment: 0,
        averageEngagement: 0,
        topTopics: new Map(),
        emotionDistribution: {},
        timestamp: new Date().toISOString()
      });
    }

    const data = this.historicalData[period].get(key);

    // Update with current real-time metrics
    data.conversationCount += this.realTimeMetrics.activeConversations;
    data.totalMessages += this.realTimeMetrics.totalMessages;

    // Update top topics
    Object.entries(this.realTimeMetrics.topicPopularity).forEach(([topic, count]) => {
      data.topTopics.set(topic, (data.topTopics.get(topic) || 0) + count);
    });

    // Reset real-time metrics
    this.realTimeMetrics.activeConversations = 0;
    this.realTimeMetrics.totalMessages = 0;
  }

  startDataCleanup() {
    setInterval(() => {
      this.cleanupOldData();
    }, 24 * 60 * 60 * 1000); // Daily cleanup
  }

  cleanupOldData() {
    const cutoffDate = moment().subtract(this.options.dataRetentionDays, 'days');

    // Clean conversation metrics
    for (const [key, data] of this.conversationMetrics) {
      if (moment(data.timestamp).isBefore(cutoffDate)) {
        this.conversationMetrics.delete(key);
      }
    }

    // Clean historical data
    Object.keys(this.historicalData).forEach(period => {
      for (const [key, data] of this.historicalData[period]) {
        if (moment(data.timestamp).isBefore(cutoffDate)) {
          this.historicalData[period].delete(key);
        }
      }
    });

    this.emit('dataCleanup', {
      timestamp: new Date().toISOString(),
      cutoffDate: cutoffDate.toISOString()
    });
  }

  // API Methods
  getConversationMetrics(conversationId) {
    return this.conversationMetrics.get(conversationId);
  }

  getPlayerEngagement(conversationId) {
    return this.playerEngagement.get(conversationId);
  }

  getDialogueEffectiveness(conversationId) {
    return this.dialogueEffectiveness.get(conversationId);
  }

  getEmotionalTrends(conversationId) {
    return this.emotionalTrends.get(conversationId);
  }

  getRelationshipMetrics(conversationId) {
    return this.relationshipMetrics.get(conversationId);
  }

  getRealTimeMetrics() {
    return { ...this.realTimeMetrics };
  }

  getHistoricalData(period, key) {
    return this.historicalData[period]?.get(key);
  }

  generateAnalyticsReport(options = {}) {
    const {
      period = 'daily',
      startDate = moment().subtract(7, 'days').toISOString(),
      endDate = moment().toISOString(),
      conversationIds = null
    } = options;

    const report = {
      period: { name: period, startDate, endDate },
      summary: this.generateSummaryReport(conversationIds),
      conversationAnalysis: this.generateConversationAnalysis(conversationIds),
      playerEngagement: this.generateEngagementReport(conversationIds),
      emotionalAnalysis: this.generateEmotionalReport(conversationIds),
      topicAnalysis: this.generateTopicReport(conversationIds),
      relationshipAnalysis: this.generateRelationshipReport(conversationIds),
      recommendations: this.generateRecommendations(),
      generatedAt: new Date().toISOString()
    };

    return report;
  }

  generateSummaryReport(conversationIds) {
    const conversations = conversationIds
      ? conversationIds.map(id => this.conversationMetrics.get(id)).filter(Boolean)
      : Array.from(this.conversationMetrics.values());

    if (conversations.length === 0) {
      return { totalConversations: 0, averageQuality: 0, totalMessages: 0 };
    }

    return {
      totalConversations: conversations.length,
      averageQuality: conversations.reduce((sum, c) => sum + (c.overall?.conversationQuality || 0), 0) / conversations.length,
      totalMessages: conversations.reduce((sum, c) => sum + (c.basic?.messageCount || 0), 0),
      averageDuration: conversations.reduce((sum, c) => sum + (c.basic?.totalDuration || 0), 0) / conversations.length,
      overallSentiment: conversations.reduce((sum, c) => sum + (c.sentiment?.overallSentiment || 0), 0) / conversations.length
    };
  }

  generateConversationAnalysis(conversationIds) {
    // Detailed conversation analysis
    return {
      averageMessageLength: 0,
      averageResponseTime: 0,
      conversationTurns: 0,
      completionRate: 0
    };
  }

  generateEngagementReport(conversationIds) {
    // Player engagement analysis
    return {
      averageEngagementScore: 0,
      mostEngagedPlayers: [],
      engagementTrends: []
    };
  }

  generateEmotionalReport(conversationIds) {
    // Emotional analysis report
    return {
      dominantEmotions: [],
      emotionalProgression: [],
      empathyIndicators: []
    };
  }

  generateTopicReport(conversationIds) {
    // Topic analysis report
    return {
      popularTopics: [],
      topicProgression: [],
      topicEngagement: {}
    };
  }

  generateRelationshipReport(conversationIds) {
    // Relationship analysis report
    return {
      strongestRelationships: [],
      relationshipTrends: [],
      communicationPatterns: {}
    };
  }

  generateRecommendations() {
    // Generate actionable recommendations based on analytics
    return [
      {
        type: 'engagement',
        priority: 'high',
        title: 'Increase Player Interaction',
        description: 'Consider adding more interactive elements to boost player engagement.',
        actionItems: ['Add choice-based dialogue', 'Implement real-time feedback', 'Create dynamic responses']
      },
      {
        type: 'emotional',
        priority: 'medium',
        title: 'Enhance Emotional Intelligence',
        description: 'Focus on improving empathy detection and response generation.',
        actionItems: ['Train emotion recognition models', 'Add more nuanced emotional responses', 'Implement mood tracking']
      }
    ];
  }

  getPerformanceMetrics() {
    return {
      uptime: process.uptime(),
      memoryUsage: process.memoryUsage(),
      cacheSize: this.conversationMetrics.size,
      processingQueue: 0,
      errorRate: 0
    };
  }

  reset() {
    this.conversationMetrics.clear();
    this.playerEngagement.clear();
    this.satisfactionScores.clear();
    this.dialogueEffectiveness.clear();
    this.emotionalTrends.clear();
    this.relationshipMetrics.clear();
    this.topicAnalysis.clear();
    this.performanceMetrics.clear();

    this.realTimeMetrics = {
      activeConversations: 0,
      totalMessages: 0,
      averageResponseTime: 0,
      sentimentDistribution: {},
      emotionDistribution: {},
      topicPopularity: {},
      playerActivity: {}
    };

    Object.values(this.historicalData).forEach(period => period.clear());
  }
}

// Analyzer helper classes
class SentimentAnalyzer {
  analyze(text) {
    // Simple sentiment analysis
    const positiveWords = ['good', 'great', 'happy', 'love', 'excellent', 'wonderful'];
    const negativeWords = ['bad', 'terrible', 'hate', 'angry', 'sad', 'awful'];

    const words = text.toLowerCase().split(/\s+/);
    let score = 0;

    words.forEach(word => {
      if (positiveWords.includes(word)) score += 1;
      if (negativeWords.includes(word)) score -= 1;
    });

    return {
      score: score / Math.max(words.length, 1),
      positive: score > 0,
      negative: score < 0,
      neutral: score === 0
    };
  }
}

class EmotionAnalyzer {
  analyze(text, emotionalState = {}) {
    const emotions = {
      happiness: 0,
      sadness: 0,
      anger: 0,
      fear: 0,
      surprise: 0,
      disgust: 0,
      trust: 0,
      anticipation: 0
    };

    // Use provided emotional state or analyze from text
    if (Object.keys(emotionalState).length > 0) {
      Object.assign(emotions, emotionalState);
    } else {
      // Simple emotion analysis from text
      const emotionWords = {
        happiness: ['happy', 'joy', 'glad', 'pleased'],
        sadness: ['sad', 'sorrow', 'grief', 'unhappy'],
        anger: ['angry', 'furious', 'mad', 'irritated'],
        fear: ['afraid', 'scared', 'terrified', 'worried'],
        surprise: ['surprised', 'amazed', 'shocked', 'astonished'],
        disgust: ['disgusted', 'revolted', 'repulsed'],
        trust: ['trust', 'believe', 'faith', 'confidence'],
        anticipation: ['excited', 'eager', 'looking', 'forward']
      };

      const words = text.toLowerCase().split(/\s+/);
      Object.entries(emotionWords).forEach(([emotion, words_list]) => {
        const count = words.filter(word => words_list.includes(word)).length;
        emotions[emotion] = Math.min(1.0, count * 0.2);
      });
    }

    return { emotions };
  }
}

class TopicAnalyzer {
  extractTopics(messages) {
    const topics = [];
    const dndTopics = [
      'quest', 'battle', 'magic', 'dragon', 'dungeon', 'treasure', 'monster',
      'party', 'guild', 'kingdom', 'prophecy', 'artifact', 'curse', 'travel',
      'inn', 'tavern', 'shop', 'training', 'level', 'experience', 'equipment'
    ];

    messages.forEach(message => {
      if (message && message.content) {
        const content = message.content.toLowerCase();
        dndTopics.forEach(topic => {
          if (content.includes(topic)) {
            topics.push(topic);
          }
        });
      }
    });

    return topics;
  }
}

class EngagementAnalyzer {
  async analyze(conversationData) {
    // Placeholder for engagement analysis
    return {
      score: 0.75,
      metrics: {
        participation: 0.8,
        responsiveness: 0.7,
        interaction: 0.75
      }
    };
  }

  async calculateEngagement(conversationData) {
    return this.analyze(conversationData);
  }
}

class EffectivenessAnalyzer {
  async analyze(conversationData) {
    // Placeholder for effectiveness analysis
    return {
      score: 0.8,
      metrics: {
        goalAchievement: 0.85,
        clarity: 0.75,
        efficiency: 0.8
      }
    };
  }

  async calculateEffectiveness(conversationData) {
    return this.analyze(conversationData);
  }
}

class RelationshipAnalyzer {
  // Placeholder for relationship analysis
}

class SatisfactionAnalyzer {
  // Placeholder for satisfaction analysis
}

module.exports = ConversationAnalyticsEngine;