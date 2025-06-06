import { useState, useEffect, useCallback } from 'react';
import type { BettingOpportunity, OpportunitiesResponse } from '../types';
import { apiService } from '../services/apiService';
import { useAuth } from '../contexts/AuthContext';

interface UseOpportunitiesReturn {
  opportunities: BettingOpportunity[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  refreshOpportunities: () => Promise<void>;
}

export const useOpportunities = (): UseOpportunitiesReturn => {
  const [opportunities, setOpportunities] = useState<BettingOpportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const { user, session } = useAuth();

  const fetchOpportunities = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Build query parameters
      const params = new URLSearchParams();
      if (searchTerm.trim()) {
        params.append('search', searchTerm.trim());
      }

      // Add user role information for backend filtering
      if (user && session) {
        // Backend will automatically filter based on authenticated user role
        console.log('Fetching opportunities for authenticated user:', user.email);
      } else {
        // Unauthenticated users get free tier data
        console.log('Fetching opportunities for unauthenticated user (free tier)');
      }

      const queryString = params.toString();
      const url = queryString ? `/api/opportunities?${queryString}` : '/api/opportunities';
      
      const response = await apiService.get<OpportunitiesResponse>(url);
      
      setOpportunities(response.opportunities || []);
      
    } catch (err) {
      console.error('Error fetching opportunities:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch opportunities');
      setOpportunities([]);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, user, session]);

  const refreshOpportunities = useCallback(async () => {
    await fetchOpportunities();
  }, [fetchOpportunities]);

  // Initial fetch and auto-refresh setup
  useEffect(() => {
    fetchOpportunities();
    
    // Set up auto-refresh every 30 seconds
    const interval = setInterval(fetchOpportunities, 30000);
    
    return () => clearInterval(interval);
  }, [fetchOpportunities]);

  return {
    opportunities,
    loading,
    error,
    searchTerm,
    setSearchTerm,
    refreshOpportunities,
  };
}; 