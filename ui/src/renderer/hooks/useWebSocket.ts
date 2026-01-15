import { useEffect, useRef, useCallback, useState } from 'react';
import type { ServerMessage, ClientCommand } from '../types';

interface UseWebSocketOptions {
  url: string;
  onMessage: (message: ServerMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  send: (command: ClientCommand) => void;
  reconnect: () => void;
}

export function useWebSocket({
  url,
  onMessage,
  onConnect,
  onDisconnect,
  reconnectInterval = 3000,
}: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const isConnectingRef = useRef(false);
  const isMountedRef = useRef(true);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    // Prevent multiple simultaneous connection attempts
    if (isConnectingRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.onclose = null; // Prevent reconnect on intentional close
      wsRef.current.close();
      wsRef.current = null;
    }

    isConnectingRef.current = true;

    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        isConnectingRef.current = false;
        if (isMountedRef.current) {
          setIsConnected(true);
          onConnect?.();
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        isConnectingRef.current = false;
        if (isMountedRef.current) {
          setIsConnected(false);
          onDisconnect?.();

          // Schedule reconnection only if still mounted
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
          reconnectTimeoutRef.current = window.setTimeout(() => {
            if (isMountedRef.current) {
              console.log('Attempting to reconnect...');
              connect();
            }
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        isConnectingRef.current = false;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as ServerMessage;
          onMessage(message);
        } catch (e) {
          console.error('Failed to parse message:', e);
        }
      };

      wsRef.current = ws;
    } catch (e) {
      console.error('Failed to create WebSocket:', e);
      isConnectingRef.current = false;
      // Schedule reconnection on error
      reconnectTimeoutRef.current = window.setTimeout(() => {
        if (isMountedRef.current) {
          connect();
        }
      }, reconnectInterval);
    }
  }, [url, onMessage, onConnect, onDisconnect, reconnectInterval]);

  const send = useCallback((command: ClientCommand) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(command));
    } else {
      console.warn('WebSocket not connected, cannot send:', command);
    }
  }, []);

  const reconnect = useCallback(() => {
    // Clear any pending reconnection
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    // Force reset connection state
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    isConnectingRef.current = false;
    connect();
  }, [connect]);

  // Connect on mount - handle React Strict Mode double-invocation
  useEffect(() => {
    isMountedRef.current = true;

    // Small delay to avoid React Strict Mode cleanup race condition
    const connectTimeout = setTimeout(() => {
      if (isMountedRef.current) {
        connect();
      }
    }, 100);

    return () => {
      // Cleanup on unmount
      isMountedRef.current = false;
      clearTimeout(connectTimeout);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      if (wsRef.current) {
        // Only close if actually connected, not if still connecting
        if (wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.onclose = null;
          wsRef.current.close();
        }
        wsRef.current = null;
      }
      isConnectingRef.current = false;
    };
  }, []); // Empty deps - only run on mount/unmount

  return { isConnected, send, reconnect };
}
