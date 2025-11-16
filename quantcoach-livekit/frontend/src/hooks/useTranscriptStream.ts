/**
 * Hook for subscribing to real-time transcript and evaluation events via SSE
 */

import { useEffect, useState, useCallback, useRef } from 'react';

export interface Transcript {
  timestamp: string;
  speaker: string;
  text: string;
  is_final: boolean;
}

export interface Evaluation {
  timestamp: string;
  window_start: string;
  window_end: string;
  transcripts_evaluated: number;
  subject_relevance: 'on_topic' | 'off_topic' | 'partially_relevant' | 'unknown';
  question_difficulty: 'easy' | 'medium' | 'hard' | 'unknown';
  interviewer_tone: 'harsh' | 'neutral' | 'encouraging' | 'unknown';
  summary: string;
  key_topics: string[];
  flags: string[];
  confidence_subject: number;
  confidence_difficulty: number;
  confidence_tone: number;
  _suppress_offtopic_alert?: boolean;
  _suppress_partially_relevant_alert?: boolean;
  _suppress_low_confidence_alert?: boolean;
  interviewer_dominance?: {
    is_dominant: boolean;
    percentage: number;
    threshold: number;
  } | null;
  coaching_flags?: Array<{
    type: string;
    severity: string;
    message: string;
    suggestion?: string;
    example_good?: string;
    example_bad?: string;
    timestamp: string;
    context_quote?: string;
  }>;
  interviewer_technique?: {
    open_ended_ratio: number;
    question_quality: string;
    follow_up_effectiveness: string;
    confidence: number;
  } | null;
}

export interface TranscriptStreamData {
  transcripts: Transcript[];
  evaluations: Evaluation[];
  isConnected: boolean;
  error: string | null;
}

interface UseTranscriptStreamOptions {
  roomName: string;
  apiBaseUrl?: string;
  autoConnect?: boolean;
}

export const useTranscriptStream = ({
  roomName,
  apiBaseUrl = 'http://localhost:8000',
  autoConnect = true,
}: UseTranscriptStreamOptions): TranscriptStreamData & {
  connect: () => void;
  disconnect: () => void;
} => {
  const [transcripts, setTranscripts] = useState<Transcript[]>([]);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (!roomName) {
      setError('Room name is required');
      return;
    }

    if (eventSourceRef.current) {
      // Already connected
      return;
    }

    try {
      const url = `${apiBaseUrl}/rooms/${roomName}/stream`;
      console.log(`[SSE] Connecting to ${url}`);

      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('[SSE] Connection opened');
        setIsConnected(true);
        setError(null);
      };

      eventSource.addEventListener('connected', (event) => {
        console.log('[SSE] Connected event received:', event.data);
      });

      eventSource.addEventListener('transcript', (event) => {
        try {
          const transcript: Transcript = JSON.parse(event.data);
          console.log('[SSE] Transcript received:', transcript);

          setTranscripts((prev) => [...prev, transcript]);
        } catch (err) {
          console.error('[SSE] Error parsing transcript:', err);
        }
      });

      eventSource.addEventListener('evaluation', (event) => {
        try {
          const evaluation: Evaluation = JSON.parse(event.data);
          console.log('[SSE] Evaluation received:', evaluation);

          setEvaluations((prev) => [...prev, evaluation]);
        } catch (err) {
          console.error('[SSE] Error parsing evaluation:', err);
        }
      });

      eventSource.addEventListener('status', (event) => {
        try {
          const status = JSON.parse(event.data);
          console.log('[SSE] Status event:', status);
        } catch (err) {
          console.error('[SSE] Error parsing status:', err);
        }
      });

      eventSource.onerror = (err) => {
        console.error('[SSE] Connection error:', err);
        setIsConnected(false);

        // Close current connection
        eventSource.close();
        eventSourceRef.current = null;

        // Attempt reconnection if enabled
        if (shouldReconnectRef.current) {
          setError('Connection lost. Reconnecting...');

          // Exponential backoff: wait 5 seconds before reconnecting
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[SSE] Attempting to reconnect...');
            connect();
          }, 5000);
        } else {
          setError('Connection lost');
        }
      };
    } catch (err) {
      console.error('[SSE] Failed to establish connection:', err);
      setError(`Connection failed: ${err}`);
      setIsConnected(false);
    }
  }, [roomName, apiBaseUrl]);

  const disconnect = useCallback(() => {
    console.log('[SSE] Disconnecting...');
    shouldReconnectRef.current = false;

    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Close event source
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    setIsConnected(false);
  }, []);

  // Auto-connect on mount and reconnect when roomName changes
  useEffect(() => {
    if (autoConnect && roomName) {
      shouldReconnectRef.current = true;

      // Disconnect from previous room if connected
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }

      // Connect to new room
      connect();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [autoConnect, roomName, connect, disconnect]);

  return {
    transcripts,
    evaluations,
    isConnected,
    error,
    connect,
    disconnect,
  };
};
