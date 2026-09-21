import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';
import toast from 'react-hot-toast';
import { SocketEvents } from '../../shared/types';

const SocketContext = createContext();

export const useSocket = () => {
  const context = useContext(SocketContext);
  if (!context) {
    throw new Error('useSocket must be used within a SocketProvider');
  }
  return context;
};

export const SocketProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [campaignId, setCampaignId] = useState(null);
  const [isDM, setIsDM] = useState(false);
  const [gameState, setGameState] = useState(null);
  const [clients, setClients] = useState([]);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // Connect to socket server
  const connect = () => {
    if (socket) return;

    const newSocket = io(process.env.REACT_APP_SERVER_URL || 'http://localhost:5001', {
      autoConnect: true,
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: maxReconnectAttempts,
      timeout: 20000,
    });

    newSocket.on('connect', () => {
      console.log('Connected to server');
      setConnected(true);
      reconnectAttempts.current = 0;
      toast.success('Connected to server');
    });

    newSocket.on('disconnect', (reason) => {
      console.log('Disconnected from server:', reason);
      setConnected(false);
      setCampaignId(null);
      setIsDM(false);
      setGameState(null);
      setClients([]);

      if (reason === 'io server disconnect') {
        // Server disconnected us, don't reconnect automatically
        toast.error('Disconnected from server');
      } else {
        // Network disconnection, will attempt to reconnect
        toast.warning('Connection lost, attempting to reconnect...');
      }
    });

    newSocket.on('connect_error', (error) => {
      console.error('Connection error:', error);
      reconnectAttempts.current++;

      if (reconnectAttempts.current >= maxReconnectAttempts) {
        toast.error('Failed to connect to server. Please refresh the page.');
      }
    });

    // Game state updates
    newSocket.on(SocketEvents.GAME_STATE_UPDATE, (newGameState) => {
      console.log('Game state updated:', newGameState);
      setGameState(newGameState);
    });

    // Character updates
    newSocket.on(SocketEvents.CHARACTER_UPDATE, (characterData) => {
      console.log('Character updated:', characterData);
      if (gameState) {
        setGameState(prev => ({
          ...prev,
          characters: {
            ...prev.characters,
            [characterData.id]: characterData
          }
        }));
      }
    });

    // Location updates
    newSocket.on(SocketEvents.LOCATION_UPDATE, (locationData) => {
      console.log('Location updated:', locationData);
      if (gameState) {
        setGameState(prev => ({
          ...prev,
          locations: {
            ...prev.locations,
            [locationData.id]: locationData
          }
        }));
      }
    });

    // Combat updates
    newSocket.on(SocketEvents.COMBAT_UPDATE, (combatData) => {
      console.log('Combat updated:', combatData);
      if (gameState) {
        setGameState(prev => ({
          ...prev,
          combat: combatData
        }));
      }
    });

    // Client management
    newSocket.on('client_joined', (clientData) => {
      console.log('Client joined:', clientData);
      setClients(prev => [...prev, clientData]);
      toast(`${clientData.isDM ? 'DM' : 'Player'} joined the campaign`);
    });

    newSocket.on('client_left', (clientData) => {
      console.log('Client left:', clientData);
      setClients(prev => prev.filter(c => c.userId !== clientData.userId));
      toast(`${clientData.isDM ? 'DM' : 'Player'} left the campaign`);
    });

    // Character actions
    newSocket.on(SocketEvents.CHARACTER_ACTION, (actionData) => {
      console.log('Character action:', actionData);
      // This will be handled by specific components
    });

    // Combat events
    newSocket.on(SocketEvents.COMBAT_START, (combatData) => {
      console.log('Combat started:', combatData);
      toast('⚔️ Combat has started!');
    });

    newSocket.on(SocketEvents.COMBAT_END, (combatData) => {
      console.log('Combat ended:', combatData);
      toast('Combat has ended');
    });

    newSocket.on(SocketEvents.INITIATIVE_ROLL, (initiativeData) => {
      console.log('Initiative rolled:', initiativeData);
      // This will be handled by combat components
    });

    // DM events
    newSocket.on(SocketEvents.INJECT_EVENT, (eventData) => {
      console.log('Event injected:', eventData);
      toast(`📜 Event: ${eventData.title}`, {
        duration: 5000,
        icon: '🎭'
      });
    });

    newSocket.on(SocketEvents.SPAWN_CREATURE, (creatureData) => {
      console.log('Creature spawned:', creatureData);
      toast(`👹 ${creatureData.name} has appeared!`, {
        duration: 4000,
        icon: '🐉'
      });
    });

    newSocket.on(SocketEvents.MODIFY_ENVIRONMENT, (modificationData) => {
      console.log('Environment modified:', modificationData);
      toast('🌍 Environment has changed', {
        duration: 3000,
        icon: '🏞️'
      });
    });

    // Character position updates
    newSocket.on('character_position_update', (positionData) => {
      console.log('Character position updated:', positionData);
      // This will be handled by map components
    });

    // Error handling
    newSocket.on('error', (errorData) => {
      console.error('Socket error:', errorData);
      toast.error(errorData.message || 'An error occurred');
    });

    // Campaign events
    newSocket.on('campaign_saved', (saveData) => {
      console.log('Campaign saved:', saveData);
      if (saveData.success) {
        toast.success('Campaign saved successfully');
      } else {
        toast.error('Failed to save campaign');
      }
    });

    setSocket(newSocket);
  };

  // Disconnect from socket server
  const disconnect = () => {
    if (socket) {
      socket.disconnect();
      setSocket(null);
      setConnected(false);
      setCampaignId(null);
      setIsDM(false);
      setGameState(null);
      setClients([]);
    }
  };

  // Join campaign
  const joinCampaign = (newCampaignId, userId, dm = false) => {
    if (!socket || !connected) {
      toast.error('Not connected to server');
      return false;
    }

    socket.emit(SocketEvents.JOIN_CAMPAIGN, {
      campaignId: newCampaignId,
      userId,
      isDM: dm
    });

    setCampaignId(newCampaignId);
    setIsDM(dm);
    return true;
  };

  // Leave campaign
  const leaveCampaign = () => {
    if (!socket || !campaignId) return;

    socket.emit(SocketEvents.LEAVE_CAMPAIGN, { campaignId });
    setCampaignId(null);
    setIsDM(false);
    setGameState(null);
    setClients([]);
  };

  // Send character action
  const sendCharacterAction = (actionData) => {
    if (!socket || !connected) {
      toast.error('Not connected to server');
      return false;
    }

    socket.emit(SocketEvents.CHARACTER_ACTION, actionData);
    return true;
  };

  // Start combat
  const startCombat = (combatData) => {
    if (!socket || !connected || !isDM) {
      toast.error('DM privileges required');
      return false;
    }

    socket.emit(SocketEvents.COMBAT_START, combatData);
    return true;
  };

  // Roll initiative
  const rollInitiative = (characterId, roll, modifier = 0) => {
    if (!socket || !connected) {
      toast.error('Not connected to server');
      return false;
    }

    socket.emit(SocketEvents.INITIATIVE_ROLL, {
      characterId,
      roll,
      modifier
    });
    return true;
  };

  // Inject event (DM only)
  const injectEvent = (eventData) => {
    if (!socket || !connected || !isDM) {
      toast.error('DM privileges required');
      return false;
    }

    socket.emit(SocketEvents.INJECT_EVENT, eventData);
    return true;
  };

  // Spawn creature (DM only)
  const spawnCreature = (creatureData) => {
    if (!socket || !connected || !isDM) {
      toast.error('DM privileges required');
      return false;
    }

    socket.emit(SocketEvents.SPAWN_CREATURE, creatureData);
    return true;
  };

  // Modify environment (DM only)
  const modifyEnvironment = (modificationData) => {
    if (!socket || !connected || !isDM) {
      toast.error('DM privileges required');
      return false;
    }

    socket.emit(SocketEvents.MODIFY_ENVIRONMENT, modificationData);
    return true;
  };

  // Update character position
  const updateCharacterPosition = (characterId, position) => {
    if (!socket || !connected) {
      toast.error('Not connected to server');
      return false;
    }

    socket.emit('character_position_update', {
      characterId,
      position
    });
    return true;
  };

  // Save campaign (DM only)
  const saveCampaign = () => {
    if (!socket || !connected || !isDM) {
      toast.error('DM privileges required');
      return false;
    }

    socket.emit(SocketEvents.CAMPAIGN_SAVE, { campaignId });
    return true;
  };

  // Connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, []);

  // Context value
  const value = {
    socket,
    connected,
    campaignId,
    isDM,
    gameState,
    clients,
    connect,
    disconnect,
    joinCampaign,
    leaveCampaign,
    sendCharacterAction,
    startCombat,
    rollInitiative,
    injectEvent,
    spawnCreature,
    modifyEnvironment,
    updateCharacterPosition,
    saveCampaign
  };

  return (
    <SocketContext.Provider value={value}>
      {children}
    </SocketContext.Provider>
  );
};