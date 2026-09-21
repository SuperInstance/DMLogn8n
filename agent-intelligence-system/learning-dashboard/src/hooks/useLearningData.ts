import { useState, useEffect, useCallback, useRef } from 'react';
import { AgentLearningMetrics, LearningDataResponse, HistoricalDataResponse } from '../types';

interface UseLearningDataOptions {
  refreshInterval?: number;
  includeHistorical?: boolean;
  onError?: (error: string) => void;
  onSuccess?: (data: AgentLearningMetrics) => void;
}

interface UseLearningDataReturn {
  data: AgentLearningMetrics | null;
  historicalData: HistoricalDataResponse['data'] | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  mutate: (newData: Partial<AgentLearningMetrics>) => void;
}

export const useLearningData = (
  agentId: string,
  timeframe: string = 'session',
  isRealTimeEnabled: boolean = true,
  options: UseLearningDataOptions = {}
): UseLearningDataReturn => {
  const {
    refreshInterval = 5000,
    includeHistorical = true,
    onError,
    onSuccess
  } = options;

  const [data, setData] = useState<AgentLearningMetrics | null>(null);
  const [historicalData, setHistoricalData] = useState<HistoricalDataResponse['data'] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    try {
      // Cancel any previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setLoading(true);
      setError(null);

      // Fetch current learning data
      const currentResponse = await fetch(
        `/api/v1/agents/${agentId}/learning-metrics?timeframe=${timeframe}`,
        {
          signal: abortControllerRef.current.signal,
          headers: {
            'Content-Type': 'application/json',
          }
        }
      );

      if (!currentResponse.ok) {
        throw new Error(`HTTP ${currentResponse.status}: ${currentResponse.statusText}`);
      }

      const currentResult: LearningDataResponse = await currentResponse.json();

      if (!currentResult.success) {
        throw new Error(currentResult.message || 'Failed to fetch learning data');
      }

      setData(currentResult.data);
      onSuccess?.(currentResult.data);

      // Fetch historical data if requested
      if (includeHistorical) {
        try {
          const historicalResponse = await fetch(
            `/api/v1/agents/${agentId}/historical-data?timeframe=${timeframe}`,
            {
              signal: abortControllerRef.current.signal,
              headers: {
                'Content-Type': 'application/json',
              }
            }
          );

          if (historicalResponse.ok) {
            const historicalResult: HistoricalDataResponse = await historicalResponse.json();
            if (historicalResult.success) {
              setHistoricalData(historicalResult.data);
            }
          }
        } catch (historicalError) {
          console.warn('Failed to fetch historical data:', historicalError);
          // Don't fail the entire request if historical data fails
        }
      }

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Request was aborted, don't treat as an error
        return;
      }

      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [agentId, timeframe, includeHistorical, onError, onSuccess]);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  const mutate = useCallback((newData: Partial<AgentLearningMetrics>) => {
    if (data) {
      const updatedData = { ...data, ...newData };
      setData(updatedData);
      onSuccess?.(updatedData);
    }
  }, [data, onSuccess]);

  // Set up real-time updates
  useEffect(() => {
    if (isRealTimeEnabled && refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isRealTimeEnabled, refreshInterval, fetchData]);

  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    data,
    historicalData,
    loading,
    error,
    refetch,
    mutate
  };
};