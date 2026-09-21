import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const useSystemStatus = (refreshInterval = 5000) => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchSystemStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/stats`);
      setSystemStatus(response.data);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch system status:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchHealthCheck = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/health`);
      return response.data;
    } catch (err) {
      console.error('Health check failed:', err);
      throw err;
    }
  }, []);

  const fetchPortals = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/portals`);
      return response.data;
    } catch (err) {
      console.error('Failed to fetch portals:', err);
      throw err;
    }
  }, []);

  const createPortal = useCallback(async (portalType, characterId = null) => {
    try {
      const payload = characterId ? { character_id: characterId } : {};
      const response = await axios.post(`${API_BASE_URL}/portals/${portalType}`, payload);
      return response.data;
    } catch (err) {
      console.error('Failed to create portal:', err);
      throw err;
    }
  }, []);

  const destroyPortal = useCallback(async (portalId) => {
    try {
      const response = await axios.delete(`${API_BASE_URL}/portals/${portalId}`);
      return response.data;
    } catch (err) {
      console.error('Failed to destroy portal:', err);
      throw err;
    }
  }, []);

  const getPortalStatus = useCallback(async (portalId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/portals/${portalId}/status`);
      return response.data;
    } catch (err) {
      console.error('Failed to get portal status:', err);
      throw err;
    }
  }, []);

  const broadcastMessage = useCallback(async (messageData) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/bridge/broadcast`, messageData);
      return response.data;
    } catch (err) {
      console.error('Failed to broadcast message:', err);
      throw err;
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchSystemStatus();
  }, [fetchSystemStatus]);

  // Set up interval for refreshing
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(fetchSystemStatus, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchSystemStatus, refreshInterval]);

  return {
    systemStatus,
    loading,
    error,
    lastUpdated,
    refetch: fetchSystemStatus,
    fetchHealthCheck,
    fetchPortals,
    createPortal,
    destroyPortal,
    getPortalStatus,
    broadcastMessage
  };
};