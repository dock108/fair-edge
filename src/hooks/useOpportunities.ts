import { useState, useEffect, useCallback } from 'react';
import { BettingOpportunity, OpportunitiesResponse } from '../types';
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
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);

  const fetchOpportunities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedMarkets.length > 0) params.append('markets', selectedMarkets.join(','));
      if (selectedSportsbooks.length > 0) params.append('sportsbooks', selectedSportsbooks.join(','));
      
      const queryString = params.toString();
      const url = queryString ? `/opportunities/ui?${queryString}` : '/opportunities/ui';
      
      const response = await apiService.get<OpportunitiesResponse>(url);
      
      setOpportunities(response.opportunities || []);
      setTotalCount(response.total_count || 0);
      setShowingCount(response.showing_count || 0);
      setLastUpdate(response.last_updated || null);
    } catch (err) {
      console.error('Error fetching opportunities:', err);
      setError('Failed to load betting opportunities');
    } finally {
      setLoading(false);
    }
  }, [searchTerm, selectedMarkets, selectedSportsbooks]);

  const refreshOpportunities = useCallback(async () => {
    await fetchOpportunities();
  }, [fetchOpportunities]);

  const connectWebSocket = useCallback(() => {
    if (websocket?.readyState === WebSocket.OPEN) return;

    try {
      const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/ev';
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'opportunities_update') {
            setOpportunities(data.opportunities || []);
            setTotalCount(data.total_count || 0);
            setShowingCount(data.showing_count || 0);
            setLastUpdate(data.last_updated || null);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (websocket?.readyState !== WebSocket.OPEN) {
            connectWebSocket();
          }
        }, 5000);
      };

      setWebsocket(ws);
    } catch (err) {
      console.error('Error connecting to WebSocket:', err);
    }
  }, [websocket]);

  const disconnectWebSocket = useCallback(() => {
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
  }, [websocket]);

  // Initial fetch
  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!websocket || websocket.readyState !== WebSocket.OPEN) {
        fetchOpportunities();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchOpportunities, websocket]);

  // Connect WebSocket on mount
  useEffect(() => {
    connectWebSocket();
    return () => disconnectWebSocket();
  }, []);

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