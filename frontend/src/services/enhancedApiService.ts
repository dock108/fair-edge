import axios from 'axios';
import type { AxiosInstance, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import type { ApiResponse } from '../types';
import { supabase } from '../lib/supabase';
import { config } from '../utils/env';

// Enhanced API service with better token management and retry logic
class EnhancedApiService {
  private api: AxiosInstance;
  private authToken: string | null = null;

  constructor() {
    this.api = axios.create({
      baseURL: '', // Use relative URLs that will be proxied by Vite
      timeout: config.apiTimeout,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  // Method to update the token from AuthContext
  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  private setupInterceptors() {
    // Request interceptor - use in-memory token first, fallback to Supabase
    this.api.interceptors.request.use(
      async (config: InternalAxiosRequestConfig) => {
        console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        
        // Use in-memory token if available, otherwise get from Supabase
        let token = this.authToken;
        if (!token) {
          try {
            const { data: { session } } = await supabase.auth.getSession();
            token = session?.access_token || null;
          } catch (error) {
            console.warn('Failed to get auth session for API request:', error);
          }
        }

        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor with retry logic for 401 errors
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        
        console.error(`❌ API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);
        
        // Handle 401 Unauthorized with token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          console.warn('🔄 401 received - attempting token refresh...');
          
          try {
            // Attempt to refresh the session
            const { data, error: refreshError } = await supabase.auth.refreshSession();
            
            if (!refreshError && data.session) {
              console.log('✅ Token refreshed successfully');
              const newToken = data.session.access_token;
              this.setAuthToken(newToken);
              
              // Retry the original request with new token
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
              }
              return this.api(originalRequest);
            } else {
              console.error('❌ Token refresh failed:', refreshError);
              // Force logout - the AuthContext will handle this via onAuthStateChange
              await supabase.auth.signOut();
              throw new Error('Session expired. Please log in again.');
            }
          } catch (refreshError) {
            console.error('❌ Error during token refresh:', refreshError);
            await supabase.auth.signOut();
            throw new Error('Session expired. Please log in again.');
          }
        }
        
        // Handle other error cases
        if (error.response?.status === 403) {
          console.warn('🚫 Forbidden request - insufficient permissions');
        } else if (error.response?.status && error.response.status >= 500) {
          console.error('🔥 Server error - backend may be down');
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Generic GET request
  async get<T = any>(url: string): Promise<T> {
    try {
      const response = await this.api.get<T>(url);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Generic POST request
  async post<T = any>(url: string, data?: any): Promise<T> {
    try {
      const response = await this.api.post<T>(url, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Generic PUT request
  async put<T = any>(url: string, data?: any): Promise<T> {
    try {
      const response = await this.api.put<T>(url, data);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Generic DELETE request
  async delete<T = any>(url: string): Promise<T> {
    try {
      const response = await this.api.delete<T>(url);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  // Specific API methods
  async getHealth() {
    return this.get('/health');
  }

  async getCurrentUser() {
    return this.get('/api/session/user');
  }

  async login(email: string, password: string) {
    return this.post('/api/session', { email, password });
  }

  async logout() {
    return this.post('/api/logout-secure');
  }

  async getOpportunities(params?: Record<string, string>) {
    const queryString = params ? '?' + new URLSearchParams(params).toString() : '';
    return this.get(`/api/opportunities${queryString}`);
  }

  async refreshOpportunities() {
    return this.post('/api/opportunities/refresh');
  }

  // Billing API methods
  async createCheckoutSession(plan?: 'basic' | 'premium'): Promise<{ checkout_url: string }> {
    return this.post('/api/billing/create-checkout-session', { plan });
  }

  async createPortalSession(): Promise<{ url: string }> {
    return this.post('/api/billing/create-portal-session');
  }

  // User info method
  async getUserInfo() {
    return this.get('/api/user-info');
  }

  // Error handling
  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError<ApiResponse>;
      
      // Extract error message from response
      const message = 
        axiosError.response?.data?.error ||
        axiosError.response?.data?.message ||
        axiosError.message ||
        'An unexpected error occurred';
      
      return new Error(message);
    }
    
    return error instanceof Error ? error : new Error('Unknown error occurred');
  }

  // Utility method to check if backend is reachable
  async checkConnection(): Promise<boolean> {
    try {
      await this.getHealth();
      return true;
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const enhancedApiService = new EnhancedApiService();