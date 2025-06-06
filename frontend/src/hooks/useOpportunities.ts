import { useState, useEffect, useCallback } from 'react';
import type { BettingOpportunity, OpportunitiesResponse } from '../types';
import { apiService } from '../services/apiService';

interface UseOpportunitiesReturn {
  opportunities: BettingOpportunity[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  showingCount: number;
  lastUpdate: string | null;
  searchTerm: string;
  selectedMarkets: string[];
  selectedSportsbooks: string[];
  setSearchTerm: (term: string) => void;
  setSelectedMarkets: (markets: string[]) => void;
  setSelectedSportsbooks: (sportsbooks: string[]) => void;
  refreshOpportunities: () => Promise<void>;
  connectWebSocket: () => void;
  disconnectWebSocket: () => void;
}

export const useOpportunities = (): UseOpportunitiesReturn => {
  const [opportunities, setOpportunities] = useState<BettingOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [showingCount, setShowingCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedMarkets, setSelectedMarkets] = useState<string[]>([]);
  const [selectedSportsbooks, setSelectedSportsbooks] = useState<string[]>([]);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  const fetchOpportunities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Build query parameters
      const params = new URLSearchParams();
      if (searchTerm.trim()) {
        params.append('search', searchTerm.trim());
      }
      if (selectedMarkets.length > 0) {
        params.append('markets', selectedMarkets.join(','));
      }
      if (selectedSportsbooks.length > 0) {
        params.append('sportsbooks', selectedSportsbooks.join(','));
      }

      const queryString = params.toString();
      const url = queryString ? `/opportunities/ui?${queryString}` : '/opportunities/ui';
      
      const response = await apiService.get<OpportunitiesResponse>(url);
      
      setOpportunities(response.opportunities || []);
      setTotalCount(response.total_available || 0);
      setShowingCount(response.shown || 0);
      setLastUpdate(response.last_updated || null);
      
    } catch (err) {
      console.error('Error fetching opportunities:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch opportunities');
      setOpportunities([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, selectedMarkets, selectedSportsbooks]);

  const refreshOpportunities = useCallback(async () => {
    await fetchOpportunities();
  }, [fetchOpportunities]);

  const connectWebSocket = useCallback(() => {
    if (wsConnection) {
      return; // Already connected
    }

    try {
      const wsUrl = import.meta.env.VITE_API_URL?.replace('http', 'ws') || 'ws://localhost:8000';
      const ws = new WebSocket(`${wsUrl}/ws/opportunities`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setWsConnection(ws);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'opportunities_update') {
            // Refresh opportunities when we get an update
            fetchOpportunities();
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnection(null);
        // Attempt to reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsConnection(null);
      };
      
    } catch (err) {
      console.error('Error connecting WebSocket:', err);
    }
  }, [wsConnection, fetchOpportunities]);

  const disconnectWebSocket = useCallback(() => {
    if (wsConnection) {
      wsConnection.close();
      setWsConnection(null);
    }
  }, [wsConnection]);

  // Initial fetch and auto-refresh setup
  useEffect(() => {
    fetchOpportunities();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchOpportunities, 30000);
    
    return () => clearInterval(interval);
  }, [fetchOpportunities]);

  // Connect WebSocket on mount
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  return {
    opportunities,
    loading,
    error,
    totalCount,
    showingCount,
    lastUpdate,
    searchTerm,
    selectedMarkets,
    selectedSportsbooks,
    setSearchTerm,
    setSelectedMarkets,
    setSelectedSportsbooks,
    refreshOpportunities,
    connectWebSocket,
    disconnectWebSocket,
  };
}; 