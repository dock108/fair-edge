// User Types
export interface User {
  id: string;
  email: string;
  role: 'free' | 'subscriber' | 'admin';
  subscription_status: string;
  created_at?: string;
  updated_at?: string;
}

// Odds Comparison Types
export interface OddsComparison {
  sportsbook: string;
  odds: string;
  link?: string;
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

// API Response Types
export interface OpportunitiesResponse {
  opportunities: BettingOpportunity[];
  total_available: number;
  shown: number;
  last_updated: string;
  role: string;
  truncated: boolean;
  limit?: string;
  features?: Record<string, any>;
}

export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
  status?: string;
}

// Component Props Types
export interface BetCardProps {
  opportunity: BettingOpportunity;
  index: number;
}

export interface NavbarProps {
  user?: User | null;
  onLogout?: () => void;
}

// Auth Context Types
export interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

// Hook Return Types
export interface UseAuthReturn extends AuthContextType {}

export interface UseOpportunitiesReturn {
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