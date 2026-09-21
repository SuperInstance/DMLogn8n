import { Router } from 'express';
import { AgentLearningMetrics, LearningDataResponse } from '../../src/types';
import { LearningDataService } from '../services/learning-data-service';
import { authMiddleware } from '../middleware/auth';

const router = Router();
const learningDataService = new LearningDataService();

// Get agent learning metrics
router.get('/agents/:agentId/learning-metrics', authMiddleware, async (req, res) => {
  try {
    const { agentId } = req.params;
    const { timeframe = 'session' } = req.query;

    // Validate timeframe
    const validTimeframes = ['session', 'day', 'week', 'month'];
    if (!validTimeframes.includes(timeframe as string)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid timeframe. Must be one of: ' + validTimeframes.join(', ')
      });
    }

    // Fetch learning metrics
    const metrics = await learningDataService.getLearningMetrics(
      agentId,
      timeframe as string,
      req.user?.id
    );

    if (!metrics) {
      return res.status(404).json({
        success: false,
        message: 'No learning data found for this agent'
      });
    }

    const response: LearningDataResponse = {
      success: true,
      data: metrics,
      timestamp: new Date()
    };

    res.json(response);
  } catch (error) {
    console.error('Error fetching learning metrics:', error);
    res.status(500).json({
      success: false,
      message: 'Internal server error',
      timestamp: new Date()
    });
  }
});

// Get historical learning data
router.get('/agents/:agentId/historical-data', authMiddleware, async (req, res) => {
  try {
    const { agentId } = req.params;
    const { timeframe = 'week' } = req.query;

    const historicalData = await learningDataService.getHistoricalData(
      agentId,
      timeframe as string,
      req.user?.id
    );

    res.json({
      success: true,
      data: historicalData,
      timeframe
    });
  } catch (error) {
    console.error('Error fetching historical data:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch historical data'
    });
  }
});

// Get before/after comparison
router.get('/agents/:agentId/comparison', authMiddleware, async (req, res) => {
  try {
    const { agentId } = req.params;
    const { beforeDate, afterDate } = req.query;

    if (!beforeDate || !afterDate) {
      return res.status(400).json({
        success: false,
        message: 'Both beforeDate and afterDate are required'
      });
    }

    const comparison = await learningDataService.getComparisonData(
      agentId,
      new Date(beforeDate as string),
      new Date(afterDate as string),
      req.user?.id
    );

    res.json({
      success: true,
      data: comparison
    });
  } catch (error) {
    console.error('Error fetching comparison data:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch comparison data'
    });
  }
});

// Export learning data
router.get('/agents/:agentId/export/:format', authMiddleware, async (req, res) => {
  try {
    const { agentId, format } = req.params;
    const { timeframe = 'month', includeCharts = 'true', includeAnalytics = 'true' } = req.query;

    const validFormats = ['pdf', 'csv', 'json', 'xlsx'];
    if (!validFormats.includes(format)) {
      return res.status(400).json({
        success: false,
        message: 'Invalid export format. Supported formats: ' + validFormats.join(', ')
      });
    }

    const exportData = await learningDataService.exportLearningData(
      agentId,
      format,
      {
        timeframe: timeframe as string,
        includeCharts: includeCharts === 'true',
        includeAnalytics: includeAnalytics === 'true'
      },
      req.user?.id
    );

    // Set appropriate headers for file download
    res.setHeader('Content-Type', exportData.contentType);
    res.setHeader('Content-Disposition', `attachment; filename="${exportData.filename}"`);
    res.setHeader('Content-Length', exportData.size.toString());

    res.send(exportData.buffer);
  } catch (error) {
    console.error('Error exporting learning data:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to export learning data'
    });
  }
});

// Update learning metrics (for real-time updates)
router.post('/agents/:agentId/learning-metrics', authMiddleware, async (req, res) => {
  try {
    const { agentId } = req.params;
    const metricsUpdate = req.body;

    // Validate the update data
    if (!metricsUpdate || typeof metricsUpdate !== 'object') {
      return res.status(400).json({
        success: false,
        message: 'Invalid metrics update data'
      });
    }

    const updatedMetrics = await learningDataService.updateLearningMetrics(
      agentId,
      metricsUpdate,
      req.user?.id
    );

    res.json({
      success: true,
      data: updatedMetrics,
      timestamp: new Date()
    });
  } catch (error) {
    console.error('Error updating learning metrics:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to update learning metrics'
    });
  }
});

// Get learning milestones
router.get('/agents/:agentId/milestones', authMiddleware, async (req, res) => {
  try {
    const { agentId } = req.params;
    const { includeAchieved = 'true', includePending = 'true' } = req.query;

    const milestones = await learningDataService.getLearningMilestones(
      agentId,
      {
        includeAchieved: includeAchieved === 'true',
        includePending: includePending === 'true'
      },
      req.user?.id
    );

    res.json({
      success: true,
      data: milestones
    });
  } catch (error) {
    console.error('Error fetching milestones:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch milestones'
    });
  }
});

// Trigger manual learning session processing
router.post('/agents/:agentId/process-session', authMiddleware, async (req, res) => {
  try {
    const { agentId } = req.params;
    const { sessionId } = req.body;

    if (!sessionId) {
      return res.status(400).json({
        success: false,
        message: 'Session ID is required'
      });
    }

    const processingResult = await learningDataService.processLearningSession(
      agentId,
      sessionId,
      req.user?.id
    );

    res.json({
      success: true,
      data: processingResult
    });
  } catch (error) {
    console.error('Error processing learning session:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to process learning session'
    });
  }
});

export default router;