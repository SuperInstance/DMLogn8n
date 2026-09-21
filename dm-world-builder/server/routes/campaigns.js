const express = require('express');
const router = express.Router();
const Campaign = require('../models/Campaign');
const { v4: uuidv4 } = require('uuid');
const logger = require('../utils/logger');
const auth = require('../middleware/auth');
const { validateCampaign } = require('../utils/validation');

// Get all campaigns for authenticated user
router.get('/', auth, async (req, res) => {
  try {
    const userId = req.user.id;
    const campaigns = await Campaign.find({
      $or: [
        { dmId: userId },
        { 'players.id': userId }
      ]
    }).sort({ updatedAt: -1 });

    res.json({
      success: true,
      data: campaigns,
      count: campaigns.length
    });
  } catch (error) {
    logger.error('Error fetching campaigns:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to fetch campaigns' }
    });
  }
});

// Get campaign by ID
router.get('/:id', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;

    const campaign = await Campaign.findOne({
      $or: [
        { id, dmId: userId },
        { id, 'players.id': userId }
      ]
    });

    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found' }
      });
    }

    res.json({
      success: true,
      data: campaign
    });
  } catch (error) {
    logger.error('Error fetching campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to fetch campaign' }
    });
  }
});

// Create new campaign
router.post('/', auth, async (req, res) => {
  try {
    const userId = req.user.id;
    const campaignData = req.body;

    // Validate campaign data
    const { error } = validateCampaign(campaignData);
    if (error) {
      return res.status(400).json({
        success: false,
        error: { message: error.details[0].message }
      });
    }

    // Generate unique ID
    const campaignId = uuidv4();

    const campaign = new Campaign({
      ...campaignData,
      id: campaignId,
      dmId: userId,
      createdAt: new Date(),
      updatedAt: new Date()
    });

    await campaign.save();

    logger.info(`Campaign created: ${campaignId} by user ${userId}`);

    res.status(201).json({
      success: true,
      data: campaign
    });
  } catch (error) {
    logger.error('Error creating campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to create campaign' }
    });
  }
});

// Update campaign
router.put('/:id', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const updateData = req.body;

    const campaign = await Campaign.findOne({ id, dmId: userId });
    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    // Validate update data if provided
    if (updateData && Object.keys(updateData).length > 0) {
      const { error } = validateCampaign(updateData);
      if (error) {
        return res.status(400).json({
          success: false,
          error: { message: error.details[0].message }
        });
      }
    }

    Object.assign(campaign, updateData);
    campaign.updatedAt = new Date();

    await campaign.save();

    logger.info(`Campaign updated: ${id} by user ${userId}`);

    res.json({
      success: true,
      data: campaign
    });
  } catch (error) {
    logger.error('Error updating campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to update campaign' }
    });
  }
});

// Delete campaign
router.delete('/:id', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;

    const campaign = await Campaign.findOne({ id, dmId: userId });
    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    await Campaign.deleteOne({ id });

    logger.info(`Campaign deleted: ${id} by user ${userId}`);

    res.json({
      success: true,
      message: 'Campaign deleted successfully'
    });
  } catch (error) {
    logger.error('Error deleting campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to delete campaign' }
    });
  }
});

// Add character to campaign
router.post('/:id/characters', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const characterData = req.body;

    const campaign = await Campaign.findOne({ id, dmId: userId });
    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    // Generate character ID
    const characterId = uuidv4();
    const character = {
      ...characterData,
      id: characterId,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    campaign.characters.push(character);
    campaign.updatedAt = new Date();
    await campaign.save();

    logger.info(`Character added to campaign: ${characterId} in campaign ${id}`);

    res.status(201).json({
      success: true,
      data: character
    });
  } catch (error) {
    logger.error('Error adding character to campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to add character to campaign' }
    });
  }
});

// Update character in campaign
router.put('/:id/characters/:characterId', auth, async (req, res) => {
  try {
    const { id, characterId } = req.params;
    const userId = req.user.id;
    const updateData = req.body;

    const campaign = await Campaign.findOne({ id, dmId: userId });
    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    const characterIndex = campaign.characters.findIndex(char => char.id === characterId);
    if (characterIndex === -1) {
      return res.status(404).json({
        success: false,
        error: { message: 'Character not found' }
      });
    }

    Object.assign(campaign.characters[characterIndex], updateData);
    campaign.characters[characterIndex].updatedAt = new Date();
    campaign.updatedAt = new Date();

    await campaign.save();

    logger.info(`Character updated: ${characterId} in campaign ${id}`);

    res.json({
      success: true,
      data: campaign.characters[characterIndex]
    });
  } catch (error) {
    logger.error('Error updating character:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to update character' }
    });
  }
});

// Add location to campaign
router.post('/:id/locations', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const locationData = req.body;

    const campaign = await Campaign.findOne({ id, dmId: userId });
    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    // Generate location ID
    const locationId = uuidv4();
    const location = {
      ...locationData,
      id: locationId,
      createdAt: new Date(),
      updatedAt: new Date()
    };

    campaign.locations.push(location);
    campaign.updatedAt = new Date();
    await campaign.save();

    logger.info(`Location added to campaign: ${locationId} in campaign ${id}`);

    res.status(201).json({
      success: true,
      data: location
    });
  } catch (error) {
    logger.error('Error adding location to campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to add location to campaign' }
    });
  }
});

// Add quest to campaign
router.post('/:id/quests', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const questData = req.body;

    const campaign = await Campaign.findOne({ id, dmId: userId });
    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    // Generate quest ID
    const questId = uuidv4();
    const quest = {
      ...questData,
      id: questId,
      createdAt: new Date()
    };

    campaign.quests.push(quest);
    campaign.updatedAt = new Date();
    await campaign.save();

    logger.info(`Quest added to campaign: ${questId} in campaign ${id}`);

    res.status(201).json({
      success: true,
      data: quest
    });
  } catch (error) {
    logger.error('Error adding quest to campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to add quest to campaign' }
    });
  }
});

// Add session to campaign
router.post('/:id/sessions', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const sessionData = req.body;

    const campaign = await Campaign.findOne({ id, dmId: userId });
    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    const session = campaign.addSession(sessionData);
    await campaign.save();

    logger.info(`Session added to campaign: ${session.id} in campaign ${id}`);

    res.status(201).json({
      success: true,
      data: session
    });
  } catch (error) {
    logger.error('Error adding session to campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to add session to campaign' }
    });
  }
});

// Get campaign statistics
router.get('/:id/stats', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;

    const campaign = await Campaign.findOne({
      $or: [
        { id, dmId: userId },
        { id, 'players.id': userId }
      ]
    });

    if (!campaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found' }
      });
    }

    const stats = {
      totalCharacters: campaign.characters.length,
      playerCharacters: campaign.characters.filter(char => char.type === 'player').length,
      npcs: campaign.npcs.length,
      locations: campaign.locations.length,
      quests: campaign.quests.length,
      activeQuests: campaign.quests.filter(quest => quest.status === 'active').length,
      completedQuests: campaign.quests.filter(quest => quest.status === 'completed').length,
      totalSessions: campaign.sessions.length,
      totalPlaytime: campaign.sessions.reduce((total, session) => {
        if (session.endTime) {
          return total + (new Date(session.endTime) - new Date(session.startTime));
        }
        return total;
      }, 0),
      campaignAge: campaign.duration,
      lastSessionDate: campaign.lastSessionDate
    };

    res.json({
      success: true,
      data: stats
    });
  } catch (error) {
    logger.error('Error fetching campaign stats:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to fetch campaign statistics' }
    });
  }
});

// Duplicate campaign
router.post('/:id/duplicate', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const { name, description } = req.body;

    const originalCampaign = await Campaign.findOne({ id, dmId: userId });
    if (!originalCampaign) {
      return res.status(404).json({
        success: false,
        error: { message: 'Campaign not found or access denied' }
      });
    }

    const duplicatedCampaign = new Campaign({
      ...originalCampaign.toObject(),
      _id: undefined,
      id: uuidv4(),
      name: name || `${originalCampaign.name} (Copy)`,
      description: description || originalCampaign.description,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastSessionDate: null,
      totalSessions: 0,
      sessions: [],
      currentState: {
        sessionActive: false,
        currentLocation: '',
        inCombat: false,
        timeOfDay: 'morning',
        dayCount: 1,
        weather: 'clear',
        season: 'spring'
      }
    });

    await duplicatedCampaign.save();

    logger.info(`Campaign duplicated: ${duplicatedCampaign.id} from ${id} by user ${userId}`);

    res.status(201).json({
      success: true,
      data: duplicatedCampaign
    });
  } catch (error) {
    logger.error('Error duplicating campaign:', error);
    res.status(500).json({
      success: false,
      error: { message: 'Failed to duplicate campaign' }
    });
  }
});

module.exports = router;