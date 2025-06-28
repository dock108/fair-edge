/**
 * Environment Configuration Utilities
 * Centralizes environment variable access and provides type safety
 */

interface AppConfig {
  // API Configuration
  apiUrl: string;
  publicUrl: string;
  
  // Environment Settings
  environment: 'development' | 'staging' | 'production';
  debug: boolean;
  
  // Feature Flags
  enableAnalytics: boolean;
  enableRealTimeUpdates: boolean;
  enablePushNotifications: boolean;
  
  // External Services
  analyticsId?: string;
  stripePublicKey?: string;
  supabaseUrl?: string;
  supabaseAnonKey?: string;
  
  // Branding
  appTitle: string;
  appDescription: string;
  twitterHandle: string;
  companyName: string;
  
  // Performance Settings
  useMockData: boolean;
  apiTimeout: number;
  dataRefreshInterval: number;
  heartbeatInterval: number;
}

/**
 * Load and validate environment configuration
 */
export const config: AppConfig = {
  // API Configuration
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  publicUrl: import.meta.env.VITE_PUBLIC_URL || 'http://localhost:5173',
  
  // Environment Settings
  environment: (import.meta.env.VITE_APP_ENV as AppConfig['environment']) || 'development',
  debug: import.meta.env.VITE_DEBUG === 'true' || import.meta.env.DEV,
  
  // Feature Flags
  enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  enableRealTimeUpdates: import.meta.env.VITE_ENABLE_REAL_TIME_UPDATES !== 'false',
  enablePushNotifications: import.meta.env.VITE_ENABLE_PUSH_NOTIFICATIONS === 'true',
  
  // External Services
  analyticsId: import.meta.env.VITE_ANALYTICS_ID,
  stripePublicKey: import.meta.env.VITE_STRIPE_PUBLIC_KEY,
  supabaseUrl: import.meta.env.VITE_SUPABASE_URL,
  supabaseAnonKey: import.meta.env.VITE_SUPABASE_ANON_KEY,
  
  // Branding
  appTitle: import.meta.env.VITE_APP_TITLE || 'Fair-Edge - Sports Betting Expected Value Analyzer',
  appDescription: import.meta.env.VITE_APP_DESCRIPTION || 'Discover profitable sports betting opportunities with advanced expected value analysis.',
  twitterHandle: import.meta.env.VITE_TWITTER_HANDLE || '@fairedge',
  companyName: import.meta.env.VITE_COMPANY_NAME || 'Fair-Edge',
  
  // Performance Settings
  useMockData: import.meta.env.VITE_USE_MOCK_DATA === 'true',
  apiTimeout: parseInt(import.meta.env.VITE_API_TIMEOUT || '30000'),
  dataRefreshInterval: parseInt(import.meta.env.VITE_DATA_REFRESH_INTERVAL || '300000'),
  heartbeatInterval: parseInt(import.meta.env.VITE_HEARTBEAT_INTERVAL || '60000'),
};

/**
 * Utility functions for environment-specific behavior
 */
export const isDevelopment = () => config.environment === 'development';
export const isProduction = () => config.environment === 'production';
export const isStaging = () => config.environment === 'staging';

/**
 * Get the full URL for a given path
 */
export const getFullUrl = (path: string = ''): string => {
  const baseUrl = config.publicUrl.replace(/\/$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
};

/**
 * Get API endpoint URL
 */
export const getApiUrl = (endpoint: string = ''): string => {
  const baseUrl = config.apiUrl.replace(/\/$/, '');
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

/**
 * Debug logging (only in development)
 */
export const debugLog = (...args: any[]): void => {
  if (config.debug) {
    console.log('[Fair-Edge Debug]', ...args);
  }
};

/**
 * Feature flag checker
 */
export const isFeatureEnabled = (feature: keyof Pick<AppConfig, 
  'enableAnalytics' | 'enableRealTimeUpdates' | 'enablePushNotifications'>
): boolean => {
  return config[feature];
};

/**
 * Configuration validation (run on app startup)
 */
export const validateConfig = (): void => {
  const requiredFields = ['apiUrl', 'publicUrl'] as const;
  const missing = requiredFields.filter(field => !config[field]);
  
  if (missing.length > 0) {
    console.error('Missing required configuration:', missing);
    if (isProduction()) {
      throw new Error(`Missing required configuration: ${missing.join(', ')}`);
    }
  }
  
  debugLog('Configuration loaded:', {
    environment: config.environment,
    apiUrl: config.apiUrl,
    publicUrl: config.publicUrl,
    features: {
      analytics: config.enableAnalytics,
      realTimeUpdates: config.enableRealTimeUpdates,
      pushNotifications: config.enablePushNotifications,
    }
  });
};