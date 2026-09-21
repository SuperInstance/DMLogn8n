import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';

export const useSocket = (namespace = '') => {
  const [socket, setSocket] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 1000;

  useEffect(() => {
    // Create socket connection
    const socketUrl = process.env.REACT_APP_SOCKET_URL || 'http://localhost:3001';
    const newSocket = io(socketUrl + namespace, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true
    });

    // Connection event handlers
    newSocket.on('connect', () => {
      console.log('Socket connected:', newSocket.id);
      setConnected(true);
      setError(null);
      reconnectAttempts.current = 0;
    });

    newSocket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
      setConnected(false);

      // Attempt to reconnect
      if (reason === 'io server disconnect' || reconnectAttempts.current < maxReconnectAttempts) {
        handleReconnect();
      }
    });

    newSocket.on('connect_error', (err) => {
      console.error('Socket connection error:', err);
      setError(err.message);
      setConnected(false);
      reconnectAttempts.current++;

      if (reconnectAttempts.current < maxReconnectAttempts) {
        setTimeout(() => {
          newSocket.connect();
        }, reconnectDelay * Math.pow(2, reconnectAttempts.current - 1)); // Exponential backoff
      }
    });

    // Trading-specific event handlers
    newSocket.on('auction_updated', (data) => {
      console.log('Auction updated:', data);
    });

    newSocket.on('bid_placed', (data) => {
      console.log('Bid placed:', data);
    });

    newSocket.on('listing_sold', (data) => {
      console.log('Listing sold:', data);
    });

    newSocket.on('price_alert', (data) => {
      console.log('Price alert:', data);
    });

    newSocket.on('market_update', (data) => {
      console.log('Market update:', data);
    });

    newSocket.on('trade_request', (data) => {
      console.log('Trade request:', data);
    });

    setSocket(newSocket);

    // Cleanup on unmount
    return () => {
      newSocket.close();
    };
  }, [namespace]);

  const handleReconnect = () => {
    if (reconnectAttempts.current < maxReconnectAttempts) {
      setTimeout(() => {
        console.log(`Attempting to reconnect... (${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
        socket?.connect();
      }, reconnectDelay * Math.pow(2, reconnectAttempts.current));
    }
  };

  const disconnect = () => {
    socket?.disconnect();
    setConnected(false);
  };

  const reconnect = () => {
    reconnectAttempts.current = 0;
    socket?.connect();
  };

  const joinRoom = (room) => {
    if (socket && connected) {
      socket.emit('join_room', room);
    }
  };

  const leaveRoom = (room) => {
    if (socket && connected) {
      socket.emit('leave_room', room);
    }
  };

  // Emit custom events with error handling
  const emit = (event, data, callback) => {
    if (socket && connected) {
      socket.emit(event, data, callback);
    } else {
      console.warn('Socket not connected, cannot emit event:', event);
      if (callback) {
        callback(new Error('Socket not connected'));
      }
    }
  };

  return {
    socket,
    connected,
    error,
    disconnect,
    reconnect,
    joinRoom,
    leaveRoom,
    emit
  };
};

export default useSocket;