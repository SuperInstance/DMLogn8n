import { useState, useEffect, useRef } from 'react';
import io from 'socket.io-client';

export const useWebSocket = (url, options = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    // Create socket connection
    socketRef.current = io(url, {
      transports: ['websocket'],
      upgrade: false,
      rememberUpgrade: false,
      ...options
    });

    const socket = socketRef.current;

    // Connection events
    socket.on('connect', () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setError(error.message);
      setIsConnected(false);
    });

    // Message handling
    socket.on('message', (message) => {
      console.log('Received message:', message);
      const newMessage = {
        id: Date.now(),
        timestamp: new Date(),
        data: message
      };
      setMessages(prev => [...prev, newMessage]);
      setLastMessage(newMessage);
    });

    // Event handling
    socket.on('event', (event) => {
      console.log('Received event:', event);
      const newEvent = {
        id: Date.now(),
        timestamp: new Date(),
        type: 'event',
        data: event
      };
      setMessages(prev => [...prev, newEvent]);
      setLastMessage(newEvent);
    });

    // Custom event handlers
    socket.on('initial_state', (state) => {
      console.log('Received initial state:', state);
      const newState = {
        id: Date.now(),
        timestamp: new Date(),
        type: 'initial_state',
        data: state
      };
      setMessages(prev => [...prev, newState]);
    });

    socket.on('heartbeat_response', (data) => {
      console.log('Heartbeat response:', data);
    });

    // Cleanup
    return () => {
      socket.disconnect();
    };
  }, [url]);

  const sendMessage = (message) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('message', message);
      return true;
    }
    return false;
  };

  const sendEvent = (eventType, data) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('event', {
        type: eventType,
        data: data,
        timestamp: new Date().toISOString()
      });
      return true;
    }
    return false;
  };

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.disconnect();
    }
  };

  const reconnect = () => {
    if (socketRef.current) {
      socketRef.current.connect();
    }
  };

  return {
    isConnected,
    messages,
    lastMessage,
    error,
    sendMessage,
    sendEvent,
    disconnect,
    reconnect,
    socket: socketRef.current
  };
};