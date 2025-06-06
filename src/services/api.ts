import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { ApiResponse, User, OpportunitiesResponse, BettingOpportunity } from '../types';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      withCredentials: true, // Include cookies for authentication
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor for adding auth headers if needed
    this.api.interceptors.request.use(
      (config) => {
        // Add any additional headers here if needed
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for handling common errors
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized - might want to redirect to login
          console.warn('Unauthorized request - user may need to log in');
        }
        return Promise.reject(error);
      }
    );
  }

  private async handleResponse<T>(promise: Promise<AxiosResponse<T>>): Promise<T> {
    try {
      const response = await promise;
      return response.data;
    } catch (error: any) {
      console.error('API Error:', error);
      throw new Error(error.response?.data?.detail || error.message || 'An error occurred');
    }
  }

  // Authentication APIs
  async getCurrentUser(): Promise<User | null> {
    try {
      return await this.handleResponse(this.api.get<User>('/me'));
    } catch (error) {
      // If user is not authenticated, return null instead of throwing
      return null;
    }
  }

  async logout(): Promise<void> {
    await this.handleResponse(this.api.post('/api/logout'));
  }

  // Opportunities APIs
  async getOpportunities(params?: {
    search?: string;
    sport?: string;
    batch_id?: string;
  }): Promise<OpportunitiesResponse> {
    const queryParams = new URLSearchParams();
    if (params?.search) queryParams.append('search', params.search);
    if (params?.sport) queryParams.append('sport', params.sport);
    if (params?.batch_id) queryParams.append('batch_id', params.batch_id);
    
    const url = `/api/opportunities${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return await this.handleResponse(this.api.get<OpportunitiesResponse>(url));
  }

  async refreshOpportunities(): Promise<ApiResponse> {
    return await this.handleResponse(this.api.post<ApiResponse>('/api/opportunities/refresh'));
  }

  // Premium APIs
  async getPremiumOpportunities(): Promise<BettingOpportunity[]> {
    return await this.handleResponse(this.api.get<BettingOpportunity[]>('/premium/opportunities'));
  }

  async getAdvancedAnalytics(): Promise<any> {
    return await this.handleResponse(this.api.get('/api/analytics/advanced'));
  }

  // Admin APIs
  async clearCache(): Promise<ApiResponse> {
    return await this.handleResponse(this.api.post<ApiResponse>('/api/clear-cache'));
  }

  async getCacheStatus(): Promise<any> {
    return await this.handleResponse(this.api.get('/api/cache-status'));
  }

  async getTaskStatus(taskId: string): Promise<any> {
    return await this.handleResponse(this.api.get(`/api/task-status/${taskId}`));
  }

  // Health check
  async healthCheck(): Promise<any> {
    return await this.handleResponse(this.api.get('/health'));
  }

  // Billing APIs
  async createCheckoutSession(): Promise<{ checkout_url: string }> {
    return await this.handleResponse(this.api.post('/api/billing/create-checkout-session'));
  }

  async manageBilling(): Promise<{ portal_url: string }> {
    return await this.handleResponse(this.api.post('/api/billing/manage'));
  }
}

// Create and export a singleton instance
export const apiService = new ApiService();
export default apiService; 