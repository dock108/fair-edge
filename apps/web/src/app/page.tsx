'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { MagnifyingGlassIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface Opportunity {
  id: string;
  event: string;
  bet_description: string;
  bet_type: string;
  ev_percentage: number;
  best_odds_source: string;
  last_updated: string;
}

interface OpportunitiesResponse {
  opportunities: Opportunity[];
  total: number;
  filters_applied: boolean;
  last_updated: string;
  response_time_ms: number;
}

export default function Dashboard() {
  const [searchTerm, setSearchTerm] = useState('');
  const [sportFilter, setSportFilter] = useState('');

  // Fetch opportunities from API
  const { data, isLoading, error, refetch } = useQuery<OpportunitiesResponse>({
    queryKey: ['opportunities', searchTerm, sportFilter],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (sportFilter) params.append('sport', sportFilter);
      
      const response = await fetch(`http://localhost:8000/api/opportunities?${params}`);
      if (!response.ok) {
        throw new Error('Failed to fetch opportunities');
      }
      return response.json();
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  });

  const getEVColorClass = (evPercentage: number) => {
    if (evPercentage >= 4.5) return 'bg-ev-excellent-bg border-ev-excellent-border text-ev-excellent';
    if (evPercentage >= 2.5) return 'bg-ev-high-bg border-ev-high-border text-ev-high';
    if (evPercentage > 0) return 'bg-ev-positive-bg border-ev-positive-border text-ev-positive';
    return 'bg-ev-neutral-bg border-ev-neutral-border text-ev-neutral';
  };

  return (
    <div className="min-h-screen bg-surface-1">
      {/* Header */}
      <header className="bg-surface-0 shadow-s border-b border-border-light">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <ChartBarIcon className="h-8 w-8 text-brand-blue-600" />
              <h1 className="text-xl font-semibold text-text-primary">
                Sports Betting +EV Analyzer
              </h1>
            </div>
            <div className="text-sm text-text-muted">
              Last updated: {data?.last_updated ? new Date(data.last_updated).toLocaleTimeString() : 'Never'}
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters Section */}
        <div className="bg-surface-0 rounded-l shadow-s p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-text-muted" />
              <input
                type="text"
                placeholder="Search teams, events, players..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-border-primary rounded-m focus:ring-2 focus:ring-brand-blue-600 focus:border-transparent"
              />
            </div>

            {/* Sport Filter */}
            <select
              value={sportFilter}
              onChange={(e) => setSportFilter(e.target.value)}
              className="w-full px-3 py-2 border border-border-primary rounded-m focus:ring-2 focus:ring-brand-blue-600 focus:border-transparent"
            >
              <option value="">All Sports</option>
              <option value="nfl">NFL</option>
              <option value="nba">NBA</option>
              <option value="mlb">MLB</option>
              <option value="nhl">NHL</option>
            </select>

            {/* Clear Filters */}
            <button
              onClick={() => {
                setSearchTerm('');
                setSportFilter('');
              }}
              className="px-4 py-2 text-sm font-medium text-text-muted hover:text-text-primary border border-border-primary rounded-m hover:bg-surface-1 transition-colors"
            >
              Clear Filters
            </button>
          </div>
        </div>

        {/* Results Summary */}
        <div className="mb-6">
          <p className="text-sm text-text-muted">
            {isLoading ? 'Loading...' : `Showing ${data?.total || 0} opportunities`}
            {data?.filters_applied && ' (filtered)'}
          </p>
        </div>

        {/* Opportunities Grid */}
        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-blue-600"></div>
          </div>
        ) : error ? (
          <div className="bg-error/10 border border-error/20 rounded-m p-6 text-center">
            <p className="text-error mb-4">Failed to load opportunities</p>
            <button
              onClick={() => refetch()}
              className="px-4 py-2 bg-brand-blue-600 text-white rounded-m hover:bg-brand-blue-700 transition-colors"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {data?.opportunities?.map((opportunity) => (
              <div
                key={opportunity.id}
                className="bg-surface-0 rounded-l shadow-s border border-border-light p-6 hover:shadow-m transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-text-primary mb-2">
                      {opportunity.event}
                    </h3>
                    <p className="text-text-secondary mb-2">
                      {opportunity.bet_description}
                    </p>
                    <div className="flex items-center space-x-4 text-sm text-text-muted">
                      <span>Type: {opportunity.bet_type}</span>
                      <span>Source: {opportunity.best_odds_source}</span>
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded-full border ${getEVColorClass(opportunity.ev_percentage)}`}>
                    <span className="font-medium">
                      +{opportunity.ev_percentage.toFixed(2)}% EV
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && data?.opportunities?.length === 0 && (
          <div className="text-center py-12">
            <ChartBarIcon className="mx-auto h-12 w-12 text-text-disabled mb-4" />
            <h3 className="text-lg font-medium text-text-primary mb-2">No opportunities found</h3>
            <p className="text-text-muted">
              {data?.filters_applied 
                ? 'Try adjusting your filters to see more results.'
                : 'Check back later for new betting opportunities.'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
