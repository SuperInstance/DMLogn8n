import { useState, useEffect, useCallback, useRef } from 'react';

interface UseWebSocketOptions {
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
  heartbeatInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: MessageEvent | null;
  sendMessage: (message: string | object) => void;
  reconnect: () => void;
  disconnect: () => void;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error';
}

export const useWebSocket = (
  url: string,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn => {
  const {
    onOpen,
    onClose,
    onError,
    onMessage,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
    heartbeatInterval = 30000
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const [connectionState, setConnectionState] = useState<UseWebSocketReturn['connectionState']>('disconnected');

  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);

  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatTimeoutRef.current) {
      clearInterval(heartbeatTimeoutRef.current);
      heartbeatTimeoutRef.current = null;
    }
  }, []);

  const startHeartbeat = useCallback(() => {
    if (heartbeatInterval > 0) {
      heartbeatTimeoutRef.current = setInterval(() => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send(JSON.stringify({ type: 'ping', timestamp: Date.now() }));
        }
      }, heartbeatInterval);
    }
  }, [heartbeatInterval]);

  const connect = useCallback(() => {
    try {
      cleanup();

      if (websocketRef.current) {
        websocketRef.current.close();
      }

      setConnectionState('connecting');

      const wsUrl = url.startsWith('ws') ? url : `ws://${window.location.host}${url}`;
      const ws = new WebSocket(wsUrl);
      websocketRef.current = ws;

      ws.onopen = (event) => {
        setIsConnected(true);
        setConnectionState('connected');
        reconnectCountRef.current = 0;
        startHeartbeat();
        onOpen?.(event);
      };

      ws.onmessage = (event) => {
        setLastMessage(event);
        onMessage?.(event);
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        setConnectionState('disconnected');
        cleanup();
        onClose?.(event);

        // Attempt to reconnect if not manually closed
        if (!event.wasClean && reconnectCountRef.current < reconnectAttempts) {
          setConnectionState('reconnecting');
          reconnectCountRef.current++;
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval * reconnectCountRef.current); // Exponential backoff
        }
      };

      ws.onerror = (event) => {
        setConnectionState('error');
        onError?.(event);
      };

    } catch (error) {
      console.error('WebSocket connection error:', error);
      setConnectionState('error');
    }
  }, [url, onOpen, onClose, onError, onMessage, reconnectAttempts, reconnectInterval, cleanup, startHeartbeat]);

  const disconnect = useCallback(() => {
    cleanup();
    if (websocketRef.current) {
      websocketRef.current.close(1000, 'Disconnected by user');
      websocketRef.current = null;
    }
    setIsConnected(false);
    setConnectionState('disconnected');
    reconnectCountRef.current = 0;
  }, [cleanup]);

  const sendMessage = useCallback((message: string | object) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      websocketRef.current.send(data);
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  const reconnect = useCallback(() => {
    reconnectCountRef.current = 0;
    disconnect();
    setTimeout(connect, 100);
  }, [disconnect, connect]);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    return disconnect;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [cleanup]);

  return {
    isConnected,
    lastMessage,
    sendMessage,
    reconnect,
    disconnect,
    connectionState
  };
};