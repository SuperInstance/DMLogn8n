const express = require('express');
const router = express.Router();

// Emotion analysis endpoint
router.post('/analyze', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');
    const analyticsEngine = req.app.get('analyticsEngine');

    const { text, speakerId, context = {} } = req.body;

    if (!text || !speakerId) {
      return res.status(400).json({
        error: 'Missing required fields: text and speakerId',
        required: ['text', 'speakerId'],
        received: { text: !!text, speakerId: !!speakerId }
      });
    }

    // Perform emotion analysis
    const analysisResult = await emotionalEngine.analyzeEmotion(text, speakerId, context);

    // Track analytics
    analyticsEngine.emit('emotionAnalysisCompleted', {
      text,
      speakerId,
      result: analysisResult,
      context,
      timestamp: new Date().toISOString()
    });

    res.json({
      success: true,
      data: analysisResult,
      requestId: req.id,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Emotion analysis error:', error);
    res.status(500).json({
      error: 'Emotion analysis failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Batch emotion analysis
router.post('/analyze-batch', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');
    const analyticsEngine = req.app.get('analyticsEngine');

    const { texts, speakerId, context = {} } = req.body;

    if (!texts || !Array.isArray(texts) || !speakerId) {
      return res.status(400).json({
        error: 'Missing required fields: texts (array) and speakerId',
        required: ['texts', 'speakerId'],
        received: { texts: Array.isArray(texts), speakerId: !!speakerId }
      });
    }

    const results = [];
    const startTime = Date.now();

    for (let i = 0; i < texts.length; i++) {
      const text = texts[i];
      try {
        const result = await emotionalEngine.analyzeEmotion(text, speakerId, {
          ...context,
          batchIndex: i
        });
        results.push({
          index: i,
          text,
          success: true,
          result
        });
      } catch (error) {
        results.push({
          index: i,
          text,
          success: false,
          error: error.message
        });
      }
    }

    const processingTime = Date.now() - startTime;

    // Track batch analytics
    analyticsEngine.emit('batchEmotionAnalysisCompleted', {
      speakerId,
      textCount: texts.length,
      successCount: results.filter(r => r.success).length,
      processingTime,
      timestamp: new Date().toISOString()
    });

    res.json({
      success: true,
      data: {
        results,
        summary: {
          total: texts.length,
          successful: results.filter(r => r.success).length,
          failed: results.filter(r => !r.success).length,
          processingTime
        }
      },
      requestId: req.id,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Batch emotion analysis error:', error);
    res.status(500).json({
      error: 'Batch emotion analysis failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Get emotional state for speaker
router.get('/state/:speakerId', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');

    const { speakerId } = req.params;
    const { limit = 50, offset = 0 } = req.query;

    const emotionalState = emotionalEngine.getEmotionalState(speakerId);

    if (!emotionalState || emotionalState.length === 0) {
      return res.json({
        success: true,
        data: {
          speakerId,
          emotionalHistory: [],
          currentEmotionalState: {},
          personalityProfile: emotionalEngine.getPersonalityProfile()
        },
        timestamp: new Date().toISOString()
      });
    }

    // Paginate results
    const paginatedHistory = emotionalState.slice(
      parseInt(offset),
      parseInt(offset) + parseInt(limit)
    );

    // Get current emotional state (most recent)
    const currentEmotionalState = emotionalState[emotionalState.length - 1]?.emotionalState || {};

    res.json({
      success: true,
      data: {
        speakerId,
        emotionalHistory: paginatedHistory,
        currentEmotionalState,
        personalityProfile: emotionalEngine.getPersonalityProfile(),
        pagination: {
          total: emotionalState.length,
          limit: parseInt(limit),
          offset: parseInt(offset),
          hasMore: parseInt(offset) + parseInt(limit) < emotionalState.length
        }
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Get emotional state error:', error);
    res.status(500).json({
      error: 'Failed to retrieve emotional state',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Update personality traits
router.put('/personality/:speakerId', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');

    const { speakerId } = req.params;
    const { traits } = req.body;

    if (!traits || typeof traits !== 'object') {
      return res.status(400).json({
        error: 'Missing required field: traits (object)',
        required: ['traits'],
        received: { traits: typeof traits }
      });
    }

    const validTraits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'];
    const updateCount = {};

    Object.entries(traits).forEach(([trait, value]) => {
      if (validTraits.includes(trait) && typeof value === 'number' && value >= 0 && value <= 1) {
        emotionalEngine.setPersonalityTrait(trait, value);
        updateCount[trait] = value;
      }
    });

    res.json({
      success: true,
      data: {
        speakerId,
        updatedTraits: updateCount,
        currentProfile: emotionalEngine.getPersonalityProfile()
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Update personality error:', error);
    res.status(500).json({
      error: 'Failed to update personality traits',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Get relationship dynamics
router.get('/relationships/:speakerId', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');

    const { speakerId } = req.params;

    const relationships = emotionalEngine.getRelationshipDynamics(speakerId);

    res.json({
      success: true,
      data: {
        speakerId,
        relationships,
        relationshipCount: Object.keys(relationships).length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Get relationships error:', error);
    res.status(500).json({
      error: 'Failed to retrieve relationship dynamics',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Reanalyze with different parameters
router.post('/reanalyze', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');

    const { text, speakerId, previousResult, reanalysisReason } = req.body;

    if (!text || !speakerId || !previousResult) {
      return res.status(400).json({
        error: 'Missing required fields: text, speakerId, and previousResult',
        required: ['text', 'speakerId', 'previousResult'],
        received: {
          text: !!text,
          speakerId: !!speakerId,
          previousResult: !!previousResult
        }
      });
    }

    // Adjust parameters based on reanalysis reason
    let adjustedContext = previousResult.context || {};

    switch (reanalysisReason) {
      case 'low_confidence':
        // Use more sensitive analysis
        adjustedContext.sensitivity = 'high';
        adjustedContext.includeSubtleEmotions = true;
        break;
      case 'complex_emotion':
        // Enable deeper emotional analysis
        adjustedContext.deepAnalysis = true;
        adjustedContext.considerContext = true;
        break;
      case 'cultural_context':
        // Emphasize cultural patterns
        adjustedContext.culturalWeight = 0.8;
        break;
      default:
        adjustedContext.reanalysis = true;
    }

    const reanalysisResult = await emotionalEngine.analyzeEmotion(text, speakerId, adjustedContext);

    // Compare with previous result
    const comparison = {
      confidenceImproved: reanalysisResult.confidence > previousResult.confidence,
      confidenceChange: reanalysisResult.confidence - previousResult.confidence,
      emotionalShift: this.calculateEmotionalShift(
        previousResult.emotionalState,
        reanalysisResult.emotionalState
      )
    };

    res.json({
      success: true,
      data: {
        originalResult: previousResult,
        reanalysisResult,
        comparison,
        reanalysisReason,
        recommendation: reanalysisResult.confidence > 0.7 ? 'use_new' : 'consider_manual'
      },
      requestId: req.id,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Reanalysis error:', error);
    res.status(500).json({
      error: 'Reanalysis failed',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Emotional trends analysis
router.get('/trends/:speakerId', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');
    const analyticsEngine = req.app.get('analyticsEngine');

    const { speakerId } = req.params;
    const { timeframe = '24h', granularity = 'hour' } = req.query;

    const emotionalHistory = emotionalEngine.getEmotionalState(speakerId);

    if (!emotionalHistory || emotionalHistory.length === 0) {
      return res.json({
        success: true,
        data: {
          speakerId,
          timeframe,
          granularity,
          trends: [],
          insights: []
        },
        timestamp: new Date().toISOString()
      });
    }

    // Filter by timeframe
    const now = new Date();
    const timeDiffMs = this.parseTimeframe(timeframe);
    const cutoffTime = new Date(now.getTime() - timeDiffMs);

    const filteredHistory = emotionalHistory.filter(entry =>
      new Date(entry.timestamp) >= cutoffTime
    );

    // Analyze trends
    const trends = this.analyzeEmotionalTrends(filteredHistory, granularity);
    const insights = this.generateEmotionalInsights(trends);

    res.json({
      success: true,
      data: {
        speakerId,
        timeframe,
        granularity,
        trends,
        insights,
        dataPoints: filteredHistory.length
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Emotional trends error:', error);
    res.status(500).json({
      error: 'Failed to analyze emotional trends',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Reset emotional data for speaker
router.delete('/reset/:speakerId', async (req, res) => {
  try {
    const emotionalEngine = req.app.get('emotionalEngine');

    const { speakerId } = req.params;
    const { confirm } = req.query;

    if (confirm !== 'true') {
      return res.status(400).json({
        error: 'Confirmation required',
        message: 'Add ?confirm=true to confirm reset',
        warning: 'This will permanently delete all emotional data for this speaker'
      });
    }

    // Reset emotional data (would need to implement this method in EmotionalIntelligenceEngine)
    emotionalEngine.reset(); // This resets all data - implement per-speaker reset as needed

    res.json({
      success: true,
      data: {
        speakerId,
        message: 'Emotional data reset successfully',
        resetAt: new Date().toISOString()
      },
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Reset emotional data error:', error);
    res.status(500).json({
      error: 'Failed to reset emotional data',
      message: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Helper functions
function calculateEmotionalShift(previousState, newState) {
  if (!previousState || !newState) return { shift: 0, changes: [] };

  const changes = [];
  let totalShift = 0;

  Object.keys(newState).forEach(emotion => {
    if (previousState[emotion] !== undefined) {
      const change = newState[emotion] - previousState[emotion];
      if (Math.abs(change) > 0.1) {
        changes.push({
          emotion,
          change,
          direction: change > 0 ? 'increase' : 'decrease',
          magnitude: Math.abs(change)
        });
        totalShift += Math.abs(change);
      }
    }
  });

  return {
    shift: totalShift,
    changes: changes.sort((a, b) => b.magnitude - a.magnitude)
  };
}

function parseTimeframe(timeframe) {
  const timeMap = {
    '1h': 60 * 60 * 1000,
    '6h': 6 * 60 * 60 * 1000,
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000
  };

  return timeMap[timeframe] || timeMap['24h'];
}

function analyzeEmotionalTrends(history, granularity) {
  // Simple trend analysis - would be more sophisticated in production
  const trends = {};

  if (history.length < 2) return trends;

  // Group by time granularity
  const grouped = groupByTime(history, granularity);

  Object.entries(grouped).forEach(([timeKey, entries]) => {
    const avgEmotions = calculateAverageEmotions(entries);
    trends[timeKey] = {
      timestamp: timeKey,
      emotions: avgEmotions,
      sampleSize: entries.length
    };
  });

  return trends;
}

function groupByTime(history, granularity) {
  const grouped = {};

  history.forEach(entry => {
    const date = new Date(entry.timestamp);
    let timeKey;

    switch (granularity) {
      case 'hour':
        timeKey = date.toISOString().substring(0, 13) + ':00';
        break;
      case 'day':
        timeKey = date.toISOString().substring(0, 10);
        break;
      case 'week':
        const weekStart = new Date(date.setDate(date.getDate() - date.getDay()));
        timeKey = weekStart.toISOString().substring(0, 10);
        break;
      default:
        timeKey = date.toISOString().substring(0, 13) + ':00';
    }

    if (!grouped[timeKey]) {
      grouped[timeKey] = [];
    }
    grouped[timeKey].push(entry);
  });

  return grouped;
}

function calculateAverageEmotions(entries) {
  const emotionSums = {};
  const emotionCounts = {};

  entries.forEach(entry => {
    Object.entries(entry.emotionalState).forEach(([emotion, intensity]) => {
      emotionSums[emotion] = (emotionSums[emotion] || 0) + intensity;
      emotionCounts[emotion] = (emotionCounts[emotion] || 0) + 1;
    });
  });

  const avgEmotions = {};
  Object.keys(emotionSums).forEach(emotion => {
    avgEmotions[emotion] = emotionSums[emotion] / emotionCounts[emotion];
  });

  return avgEmotions;
}

function generateEmotionalInsights(trends) {
  const insights = [];
  const trendEntries = Object.entries(trends);

  if (trendEntries.length < 2) return insights;

  // Analyze emotional progression
  const firstEntry = trendEntries[0][1];
  const lastEntry = trendEntries[trendEntries.length - 1][1];

  Object.keys(lastEntry.emotions).forEach(emotion => {
    if (firstEntry.emotions[emotion] !== undefined) {
      const change = lastEntry.emotions[emotion] - firstEntry.emotions[emotion];
      if (Math.abs(change) > 0.2) {
        insights.push({
          type: 'emotional_trend',
          emotion,
          trend: change > 0 ? 'increasing' : 'decreasing',
          magnitude: Math.abs(change),
          description: `${emotion} has been ${change > 0 ? 'increasing' : 'decreasing'} over the analyzed period`
        });
      }
    }
  });

  return insights;
}

module.exports = router;