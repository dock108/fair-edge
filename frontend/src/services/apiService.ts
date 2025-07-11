import axios from 'axios';
import type { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import type { ApiResponse } from '../types';
import { supabase } from '../lib/supabase';
import { config } from '../utils/env';

class ApiService {
  private api: AxiosInstance;

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

  private setupInterceptors() {
    // Request interceptor
    this.api.interceptors.request.use(
      async (config) => {
        console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        
        // Add authentication token if available
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.access_token) {
            config.headers.Authorization = `Bearer ${session.access_token}`;
          }
        } catch (error) {
          console.warn('Failed to get auth session for API request:', error);
        }
        
        return config;
      },
      (error) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response: AxiosResponse) => {
        console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        return response;
      },
      (error: AxiosError) => {
        console.error(`❌ API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);
        
        // Handle specific error cases
        if (error.response?.status === 401) {
          console.warn('🔒 Unauthorized request - user may need to login');
        } else if (error.response?.status === 403) {
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
export const apiService = new ApiService(); 