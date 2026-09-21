import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { useSocket } from './SocketContext';

const CampaignContext = createContext();

export const useCampaign = () => {
  const context = useContext(CampaignContext);
  if (!context) {
    throw new Error('useCampaign must be used within a CampaignProvider');
  }
  return context;
};

export const CampaignProvider = ({ children }) => {
  const [campaigns, setCampaigns] = useState([]);
  const [currentCampaign, setCurrentCampaign] = useState(null);
  const [loading, setLoading] = useState(false);
  const [characters, setCharacters] = useState([]);
  const [locations, setLocations] = useState([]);
  const [quests, setQuests] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [npcs, setNpcs] = useState([]);
  const [items, setItems] = useState([]);

  const { gameState, socket, connected, joinCampaign, leaveCampaign } = useSocket();

  // Fetch all campaigns for user
  const fetchCampaigns = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/campaigns');

      if (response.data.success) {
        setCampaigns(response.data.data);
      } else {
        toast.error('Failed to fetch campaigns');
      }
    } catch (error) {
      console.error('Error fetching campaigns:', error);
      toast.error('Failed to fetch campaigns');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch single campaign
  const fetchCampaign = useCallback(async (campaignId) => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/campaigns/${campaignId}`);

      if (response.data.success) {
        const campaign = response.data.data;
        setCurrentCampaign(campaign);
        setCharacters(campaign.characters || []);
        setLocations(campaign.locations || []);
        setQuests(campaign.quests || []);
        setSessions(campaign.sessions || []);
        setNpcs(campaign.npcs || []);
        setItems(campaign.items || []);
        return campaign;
      } else {
        toast.error('Failed to fetch campaign');
        return null;
      }
    } catch (error) {
      console.error('Error fetching campaign:', error);
      toast.error('Failed to fetch campaign');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Create new campaign
  const createCampaign = useCallback(async (campaignData) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/campaigns', campaignData);

      if (response.data.success) {
        const newCampaign = response.data.data;
        setCampaigns(prev => [newCampaign, ...prev]);
        toast.success('Campaign created successfully');
        return { success: true, data: newCampaign };
      } else {
        toast.error(response.data.error?.message || 'Failed to create campaign');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to create campaign';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  // Update campaign
  const updateCampaign = useCallback(async (campaignId, updateData) => {
    try {
      setLoading(true);
      const response = await axios.put(`/api/campaigns/${campaignId}`, updateData);

      if (response.data.success) {
        const updatedCampaign = response.data.data;
        setCurrentCampaign(updatedCampaign);
        setCampaigns(prev =>
          prev.map(campaign =>
            campaign.id === campaignId ? updatedCampaign : campaign
          )
        );
        toast.success('Campaign updated successfully');
        return { success: true, data: updatedCampaign };
      } else {
        toast.error(response.data.error?.message || 'Failed to update campaign');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to update campaign';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, []);

  // Delete campaign
  const deleteCampaign = useCallback(async (campaignId) => {
    try {
      setLoading(true);
      const response = await axios.delete(`/api/campaigns/${campaignId}`);

      if (response.data.success) {
        setCampaigns(prev => prev.filter(campaign => campaign.id !== campaignId));
        if (currentCampaign?.id === campaignId) {
          setCurrentCampaign(null);
          setCharacters([]);
          setLocations([]);
          setQuests([]);
          setSessions([]);
          setNpcs([]);
          setItems([]);
        }
        toast.success('Campaign deleted successfully');
        return { success: true };
      } else {
        toast.error(response.data.error?.message || 'Failed to delete campaign');
        return { success: false, error: response.data.error };
      }
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message || 'Failed to delete campaign';
      toast.error(errorMessage);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [currentCampaign]);

  // Join campaign session
  const joinCampaignSession = useCallback(async (campaignId, userId, isDM = false) => {
    try {
      // Fetch campaign data
      await fetchCampaign(campaignId);

      // Join socket room
      if (connected && socket) {
        const success = joinCampaign(campaignId, userId, isDM);
        if (success) {
          toast.success(`Joined campaign session${isDM ? ' as DM' : ''}`);
          return { success: true };
        } else {
          toast.error('Failed to join campaign session');
          return { success: false };
        }
      } else {
        toast.error('Not connected to server');
        return { success: false };
      }
    } catch (error) {
      console.error('Error joining campaign session:', error);
      toast.error('Failed to join campaign session');
      return { success: false };
    }
  }, [fetchCampaign, connected, socket, joinCampaign]);

  // Leave campaign session
  const leaveCampaignSession = useCallback(() => {
    if (currentCampaign) {
      leaveCampaign();
      setCurrentCampaign(null);
      setCharacters([]);
      setLocations([]);
      setQuests([]);
      setSessions([]);
      setNpcs([]);
      setItems([]);
      toast.success('Left campaign session');
    }
  }, [currentCampaign, leaveCampaign]);

  // Character management
  const addCharacter = useCallback(async (campaignId, characterData) => {
    try {
      const response = await axios.post(`/api/campaigns/${campaignId}/characters`, characterData);

      if (response.data.success) {
        const newCharacter = response.data.data;
        setCharacters(prev => [...prev, newCharacter]);

        if (currentCampaign?.id === campaignId) {
          setCurrentCampaign(prev => ({
            ...prev,
            characters: [...prev.characters, newCharacter]
          }));
        }

        toast.success('Character added successfully');
        return { success: true, data: newCharacter };
      } else {
        toast.error('Failed to add character');
        return { success: false };
      }
    } catch (error) {
      toast.error('Failed to add character');
      return { success: false };
    }
  }, [currentCampaign]);

  const updateCharacter = useCallback(async (campaignId, characterId, updateData) => {
    try {
      const response = await axios.put(`/api/campaigns/${campaignId}/characters/${characterId}`, updateData);

      if (response.data.success) {
        const updatedCharacter = response.data.data;
        setCharacters(prev =>
          prev.map(char => char.id === characterId ? updatedCharacter : char)
        );

        if (currentCampaign?.id === campaignId) {
          setCurrentCampaign(prev => ({
            ...prev,
            characters: prev.characters.map(char =>
              char.id === characterId ? updatedCharacter : char
            )
          }));
        }

        toast.success('Character updated successfully');
        return { success: true, data: updatedCharacter };
      } else {
        toast.error('Failed to update character');
        return { success: false };
      }
    } catch (error) {
      toast.error('Failed to update character');
      return { success: false };
    }
  }, [currentCampaign]);

  // Location management
  const addLocation = useCallback(async (campaignId, locationData) => {
    try {
      const response = await axios.post(`/api/campaigns/${campaignId}/locations`, locationData);

      if (response.data.success) {
        const newLocation = response.data.data;
        setLocations(prev => [...prev, newLocation]);

        if (currentCampaign?.id === campaignId) {
          setCurrentCampaign(prev => ({
            ...prev,
            locations: [...prev.locations, newLocation]
          }));
        }

        toast.success('Location added successfully');
        return { success: true, data: newLocation };
      } else {
        toast.error('Failed to add location');
        return { success: false };
      }
    } catch (error) {
      toast.error('Failed to add location');
      return { success: false };
    }
  }, [currentCampaign]);

  // Quest management
  const addQuest = useCallback(async (campaignId, questData) => {
    try {
      const response = await axios.post(`/api/campaigns/${campaignId}/quests`, questData);

      if (response.data.success) {
        const newQuest = response.data.data;
        setQuests(prev => [...prev, newQuest]);

        if (currentCampaign?.id === campaignId) {
          setCurrentCampaign(prev => ({
            ...prev,
            quests: [...prev.quests, newQuest]
          }));
        }

        toast.success('Quest added successfully');
        return { success: true, data: newQuest };
      } else {
        toast.error('Failed to add quest');
        return { success: false };
      }
    } catch (error) {
      toast.error('Failed to add quest');
      return { success: false };
    }
  }, [currentCampaign]);

  // Session management
  const addSession = useCallback(async (campaignId, sessionData) => {
    try {
      const response = await axios.post(`/api/campaigns/${campaignId}/sessions`, sessionData);

      if (response.data.success) {
        const newSession = response.data.data;
        setSessions(prev => [...prev, newSession]);

        if (currentCampaign?.id === campaignId) {
          setCurrentCampaign(prev => ({
            ...prev,
            sessions: [...prev.sessions, newSession]
          }));
        }

        toast.success('Session added successfully');
        return { success: true, data: newSession };
      } else {
        toast.error('Failed to add session');
        return { success: false };
      }
    } catch (error) {
      toast.error('Failed to add session');
      return { success: false };
    }
  }, [currentCampaign]);

  // Sync with game state from socket
  useEffect(() => {
    if (gameState && currentCampaign && gameState.campaignId === currentCampaign.id) {
      if (gameState.characters) {
        setCharacters(Array.from(gameState.characters.values()));
      }
      if (gameState.locations) {
        setLocations(Array.from(gameState.locations.values()));
      }
      if (gameState.combat) {
        // Update combat state in current campaign
        setCurrentCampaign(prev => ({
          ...prev,
          currentState: {
            ...prev.currentState,
            inCombat: true,
            combat: gameState.combat
          }
        }));
      }
    }
  }, [gameState, currentCampaign]);

  // Initial fetch
  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  const value = {
    campaigns,
    currentCampaign,
    loading,
    characters,
    locations,
    quests,
    sessions,
    npcs,
    items,
    fetchCampaigns,
    fetchCampaign,
    createCampaign,
    updateCampaign,
    deleteCampaign,
    joinCampaignSession,
    leaveCampaignSession,
    addCharacter,
    updateCharacter,
    addLocation,
    addQuest,
    addSession,
    setCharacters,
    setLocations,
    setQuests,
    setSessions,
    setNpcs,
    setItems
  };

  return (
    <CampaignContext.Provider value={value}>
      {children}
    </CampaignContext.Provider>
  );
};