// User and Authentication Types
export interface User {
  id: string;
  email: string;
  role: 'free' | 'subscriber' | 'admin';
  subscription_status: 'active' | 'inactive' | 'cancelled' | null;
}

// Betting Opportunity Types (matches processed UI data from backend)
export interface BettingOpportunity {
  event: string;
  bet_description: string;
  bet_type: string; // Processed market display name
  ev_percentage: number; // Already converted to percentage 
  ev_classification: 'high' | 'positive' | 'neutral';
  available_odds: OddsComparison[]; // Parsed and sorted odds
  fair_odds?: string;
  best_available_odds?: string;
  best_odds_source?: string;
  recommended_posting_odds?: string;
  recommended_book?: string;
  action_link?: string;
  sport?: string;
  _original?: any; // For debugging
}

export interface OddsComparison {
  bookmaker?: string;
  sportsbook?: string;
  odds: string;
  link?: string;
}

// API Response Types  
export interface OpportunitiesResponse {
  opportunities: BettingOpportunity[];
  total_available?: number;
  total_count?: number;
  shown?: number;
  showing_count?: number;
  last_update?: string;
  last_updated?: string;
  role: string;
  truncated?: boolean;
  limit?: string;
  filters_applied?: {
    search?: string;
    sport?: string;
  };
  analytics?: any;
  data_source?: string;
  is_guest?: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

// Component Props
export interface BetCardProps {
  opportunity: BettingOpportunity;
  index: number;
}

export interface NavbarProps {
  user?: User | null;
  isLoading?: boolean;
}

// Filter and Search Types
export interface FiltersState {
  search: string;
  sport: string;
  sortBy: 'ev' | 'recent' | 'sport';
}

// Environment Variables
export interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_FRONTEND_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
} 