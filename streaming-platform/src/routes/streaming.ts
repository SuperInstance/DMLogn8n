import express from 'express';
import { StreamingService } from '@/services/streaming';
import { OBSController } from '@/services/obs';
import { logger } from '@/utils/logger';

const router = express.Router();

// Start streaming
router.post('/start', async (req, res) => {
  try {
    const { platforms, title, description, tags, category } = req.body;

    if (!platforms || !Array.isArray(platforms) || platforms.length === 0) {
      return res.status(400).json({ error: 'Platforms array is required' });
    }

    const streamConfigs = platforms.map(platform => ({
      platform,
      title: title || 'Live D&D Session',
      description: description || 'Professional D&D streaming with interactive elements',
      tags: tags || ['dnd', 'tabletop', 'rpg', 'gaming'],
      category: category || 'Dungeons & Dragons',
      latency: 'normal',
      quality: '1080p',
      bitrate: 6000,
      fps: 60
    }));

    const result = await StreamingService.startStream(streamConfigs);

    res.json({
      success: true,
      data: result
    });

  } catch (error) {
    logger.error('Failed to start stream:', error);
    res.status(500).json({ error: 'Failed to start stream', details: error.message });
  }
});

// Stop streaming
router.post('/stop', async (req, res) => {
  try {
    const { sessionId } = req.body;

    const result = await StreamingService.stopStream(sessionId);

    res.json({
      success: true,
      data: result
    });

  } catch (error) {
    logger.error('Failed to stop stream:', error);
    res.status(500).json({ error: 'Failed to stop stream', details: error.message });
  }
});

// Get stream status
router.get('/status/:sessionId?', async (req, res) => {
  try {
    const { sessionId } = req.params;

    const status = await StreamingService.getStreamStatus(sessionId);

    res.json({
      success: true,
      data: status
    });

  } catch (error) {
    logger.error('Failed to get stream status:', error);
    res.status(500).json({ error: 'Failed to get stream status', details: error.message });
  }
});

// Scene management
router.get('/scenes', async (req, res) => {
  try {
    const scenes = await OBSController.getScenes();
    const currentScene = await OBSController.getCurrentScene();

    res.json({
      success: true,
      data: {
        scenes,
        currentScene
      }
    });

  } catch (error) {
    logger.error('Failed to get scenes:', error);
    res.status(500).json({ error: 'Failed to get scenes', details: error.message });
  }
});

router.post('/scenes/switch', async (req, res) => {
  try {
    const { sceneName } = req.body;

    if (!sceneName) {
      return res.status(400).json({ error: 'Scene name is required' });
    }

    await OBSController.switchScene(sceneName);

    res.json({
      success: true,
      message: `Switched to scene: ${sceneName}`
    });

  } catch (error) {
    logger.error('Failed to switch scene:', error);
    res.status(500).json({ error: 'Failed to switch scene', details: error.message });
  }
});

// OBS control
router.post('/obs/start-streaming', async (req, res) => {
  try {
    await OBSController.startStreaming();

    res.json({
      success: true,
      message: 'OBS streaming started'
    });

  } catch (error) {
    logger.error('Failed to start OBS streaming:', error);
    res.status(500).json({ error: 'Failed to start OBS streaming', details: error.message });
  }
});

router.post('/obs/stop-streaming', async (req, res) => {
  try {
    await OBSController.stopStreaming();

    res.json({
      success: true,
      message: 'OBS streaming stopped'
    });

  } catch (error) {
    logger.error('Failed to stop OBS streaming:', error);
    res.status(500).json({ error: 'Failed to stop OBS streaming', details: error.message });
  }
});

router.post('/obs/start-recording', async (req, res) => {
  try {
    await OBSController.startRecording();

    res.json({
      success: true,
      message: 'OBS recording started'
    });

  } catch (error) {
    logger.error('Failed to start OBS recording:', error);
    res.status(500).json({ error: 'Failed to start OBS recording', details: error.message });
  }
});

router.post('/obs/stop-recording', async (req, res) => {
  try {
    await OBSController.stopRecording();

    res.json({
      success: true,
      message: 'OBS recording stopped'
    });

  } catch (error) {
    logger.error('Failed to stop OBS recording:', error);
    res.status(500).json({ error: 'Failed to stop OBS recording', details: error.message });
  }
});

// Source control
router.post('/obs/sources/:sourceName/visibility', async (req, res) => {
  try {
    const { sourceName } = req.params;
    const { visible } = req.body;

    if (typeof visible !== 'boolean') {
      return res.status(400).json({ error: 'Visible property must be a boolean' });
    }

    await OBSController.setSourceVisibility(sourceName, visible);

    res.json({
      success: true,
      message: `Source ${sourceName} visibility set to ${visible}`
    });

  } catch (error) {
    logger.error('Failed to set source visibility:', error);
    res.status(500).json({ error: 'Failed to set source visibility', details: error.message });
  }
});

router.post('/obs/sources/:sourceName/settings', async (req, res) => {
  try {
    const { sourceName } = req.params;
    const { settings, sourceType } = req.body;

    if (!settings || !sourceType) {
      return res.status(400).json({ error: 'Settings and sourceType are required' });
    }

    await OBSController.setSourceSettings(sourceName, sourceType, settings);

    res.json({
      success: true,
      message: `Source ${sourceName} settings updated`
    });

  } catch (error) {
    logger.error('Failed to update source settings:', error);
    res.status(500).json({ error: 'Failed to update source settings', details: error.message });
  }
});

// Browser source control
router.post('/obs/sources/:sourceName/url', async (req, res) => {
  try {
    const { sourceName } = req.params;
    const { url } = req.body;

    if (!url) {
      return res.status(400).json({ error: 'URL is required' });
    }

    await OBSController.setBrowserSourceURL(sourceName, url);

    res.json({
      success: true,
      message: `Browser source ${sourceName} URL updated to ${url}`
    });

  } catch (error) {
    logger.error('Failed to update browser source URL:', error);
    res.status(500).json({ error: 'Failed to update browser source URL', details: error.message });
  }
});

// Text source control
router.post('/obs/sources/:sourceName/text', async (req, res) => {
  try {
    const { sourceName } = req.params;
    const { text } = req.body;

    if (typeof text !== 'string') {
      return res.status(400).json({ error: 'Text must be a string' });
    }

    await OBSController.setTextSourceText(sourceName, text);

    res.json({
      success: true,
      message: `Text source ${sourceName} updated`
    });

  } catch (error) {
    logger.error('Failed to update text source:', error);
    res.status(500).json({ error: 'Failed to update text source', details: error.message });
  }
});

// Screenshot
router.post('/obs/screenshot', async (req, res) => {
  try {
    const screenshot = await OBSController.takeScreenshot();

    res.json({
      success: true,
      data: { screenshot }
    });

  } catch (error) {
    logger.error('Failed to take screenshot:', error);
    res.status(500).json({ error: 'Failed to take screenshot', details: error.message });
  }
});

// Stream configuration
router.get('/config', async (req, res) => {
  try {
    const config = {
      obsConnected: OBSController.isConnected(),
      platforms: {
        twitch: !!process.env.TWITCH_CLIENT_ID,
        youtube: !!process.env.YOUTUBE_API_KEY,
        facebook: !!process.env.FACEBOOK_APP_ID,
        tiktok: !!process.env.TIKTOK_CLIENT_ID
      },
      overlays: {
        diceRoller: true,
        characterDisplay: true,
        chatOverlay: true,
        donationAlerts: true,
        scoreboard: true
      }
    };

    res.json({
      success: true,
      data: config
    });

  } catch (error) {
    logger.error('Failed to get config:', error);
    res.status(500).json({ error: 'Failed to get config', details: error.message });
  }
});

export default router;