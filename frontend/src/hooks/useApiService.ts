import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { enhancedApiService } from '../services/enhancedApiService';

/**
 * Hook that integrates the enhanced API service with the auth context
 * This ensures the API service always has the latest access token
 */
export const useApiService = () => {
  const { accessToken } = useAuth();

  useEffect(() => {
    // Update the API service with the latest token whenever it changes
    enhancedApiService.setAuthToken(accessToken);
  }, [accessToken]);

  return enhancedApiService;
};