import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useOpportunities } from '../hooks/useOpportunities';
import BetCard from '../components/BetCard';

const DashboardPage: React.FC = () => {
  const { user, isAdmin, isSubscriber } = useAuth();
  const {
    opportunities,
    isLoading,
    error,
    lastUpdated,
    totalCount,
    showingCount,
    filters,
    updateFilters,
    clearFilters,
    refreshOpportunities
  } = useOpportunities();

  const [searchInput, setSearchInput] = useState('');

  // Update document title
  useEffect(() => {
    document.title = 'Sports Betting Dashboard - Live Expected Value Analysis';
  }, []);

  // Handle search input changes with debouncing
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      updateFilters({ search: searchInput });
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [searchInput, updateFilters]);

  const handleSportFilter = (sport: string) => {
    updateFilters({ sport: sport === filters.sport ? '' : sport });
  };

  const handleClearSearch = () => {
    setSearchInput('');
    updateFilters({ search: '' });
  };

  const handleRefresh = () => {
    refreshOpportunities();
  };

  const formatLastUpdated = (timestamp: string) => {
    if (!timestamp) return 'Just now';
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins === 1) return '1 minute ago';
      if (diffMins < 60) return `${diffMins} minutes ago`;
      
      return date.toLocaleTimeString();
    } catch {
      return 'Just now';
    }
  };

  const availableSports = Array.from(new Set(opportunities.map(opp => opp.sport))).filter(Boolean);

  return (
    <>
      {/* Skip Link for Accessibility */}
      <a href="#main-content" className="skip-link">Skip to main content</a>

      {/* Admin Debug Panel (optional - can be implemented later) */}
      {isAdmin && (
        <div className="admin-debug-panel">
          <div className="content-wrap">
            <div className="debug-header">
              <h2><i className="fas fa-cog me-2"></i>Developer Debug Mode</h2>
              <p className="text-muted">Debug information panel for administrators.</p>
            </div>
            <div className="debug-data">
              <strong>Total Opportunities:</strong> {totalCount}<br/>
              <strong>Showing:</strong> {showingCount}<br/>
              <strong>Last Updated:</strong> {formatLastUpdated(lastUpdated)}<br/>
              <strong>Filters Active:</strong> {Object.values(filters).filter(Boolean).length}
            </div>
          </div>
        </div>
      )}

      {/* Sticky Top Shell with Title */}
      <header className="top-shell" id="top-shell">
        <div className="content-wrap">
          <div className="top-shell__content">
            <div className="flex items-center gap-3">
              <h1 className="top-shell__title">Sports Betting +EV Analyzer</h1>
              <span className="sr-only">Educational odds analysis and comparison tool for research and educational purposes only</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Wrapper */}
      <div className="content-wrap">
        
        {/* Free Tier Upgrade Banner */}
        {user && !isSubscriber && (
          <div className="alert alert-info alert-dismissible fade show" role="alert" style={{ marginTop: 'var(--sp-4)' }}>
            <strong><i className="fas fa-star me-1"></i>Upgrade to Premium →</strong> 
            You're seeing main lines only (moneyline, spreads, totals). 
            <strong>Upgrade to unlock props, alt lines, and live markets.</strong>
            <a href="/pricing" className="alert-link">See plans</a>.
            <button type="button" className="btn-close" data-bs-dismiss="alert" aria-label="Close upgrade banner"></button>
          </div>
        )}

        {/* Search and Filter Controls */}
        <div className="filters-section" style={{ marginTop: 'var(--sp-4)', marginBottom: 'var(--sp-4)' }}>
          <div className="card">
            <div className="card-body">
              <div className="row g-3 align-items-center">
                
                {/* Search Box */}
                <div className="col-md-4">
                  <label htmlFor="filter-search" className="sr-only">Search teams, events, players</label>
                  <div className="input-group">
                    <input 
                      type="text" 
                      id="filter-search"
                      value={searchInput}
                      onChange={(e) => setSearchInput(e.target.value)}
                      placeholder="Search teams, events, players..."
                      className="form-control search-input"
                      aria-describedby="search-help"
                    />
                    <button 
                      className="btn btn-outline-secondary" 
                      type="button" 
                      onClick={handleClearSearch}
                      aria-label="Clear search"
                    >
                      <i className="fas fa-times" aria-hidden="true"></i>
                    </button>
                  </div>
                </div>

                {/* Sport Filter */}
                <div className="col-md-4">
                  <label htmlFor="filter-sport" className="sr-only">Filter by sport</label>
                  <select 
                    id="filter-sport"
                    className="form-select"
                    value={filters.sport}
                    onChange={(e) => handleSportFilter(e.target.value)}
                  >
                    <option value="">All Sports</option>
                    {availableSports.map(sport => (
                      <option key={sport} value={sport}>{sport}</option>
                    ))}
                  </select>
                </div>

                {/* Refresh Button */}
                <div className="col-md-4">
                  <button 
                    onClick={handleRefresh}
                    className="btn btn-outline-primary"
                    disabled={isLoading}
                  >
                    <i className={`fas fa-sync-alt me-1 ${isLoading ? 'fa-spin' : ''}`}></i>
                    {isLoading ? 'Refreshing...' : 'Refresh Data'}
                  </button>
                  
                  {Object.values(filters).some(Boolean) && (
                    <button 
                      onClick={clearFilters}
                      className="btn btn-outline-secondary ms-2"
                    >
                      <i className="fas fa-times me-1"></i>
                      Clear Filters
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Status Section */}
        <div className="status-section" style={{ marginBottom: 'var(--sp-4)' }}>
          <div className="row align-items-center">
            <div className="col-md-8">
              <div className="status-info">
                {isLoading ? (
                  <p className="status-text">
                    <i className="fas fa-spinner fa-spin me-2"></i>
                    Loading opportunities...
                  </p>
                ) : error ? (
                  <p className="status-text text-danger">
                    <i className="fas fa-exclamation-triangle me-2"></i>
                    {error}
                  </p>
                ) : (
                  <p className="status-text">
                    <i className="fas fa-chart-line me-2"></i>
                    Showing <strong>{showingCount}</strong> of <strong>{totalCount}</strong> opportunities
                    {Object.values(filters).some(Boolean) && <span className="text-muted"> (filtered)</span>}
                  </p>
                )}
              </div>
            </div>
            <div className="col-md-4 text-end">
              <small className="text-muted">
                <i className="fas fa-clock me-1"></i>
                Last updated: <strong>{formatLastUpdated(lastUpdated)}</strong>
              </small>
            </div>
          </div>
        </div>

        {/* Opportunities Grid */}
        <main id="main-content" role="main">
          {isLoading && opportunities.length === 0 ? (
            <div className="text-center py-5">
              <i className="fas fa-spinner fa-spin fa-2x text-primary mb-3"></i>
              <p className="text-muted">Loading opportunities...</p>
            </div>
          ) : error ? (
            <div className="text-center py-5">
              <i className="fas fa-exclamation-triangle fa-2x text-danger mb-3"></i>
              <h3>Unable to Load Opportunities</h3>
              <p className="text-muted">{error}</p>
              <button onClick={handleRefresh} className="btn btn-primary">
                Try Again
              </button>
            </div>
          ) : opportunities.length === 0 ? (
            <div className="text-center py-5">
              <i className="fas fa-search fa-2x text-muted mb-3"></i>
              <h3>No Opportunities Found</h3>
              <p className="text-muted">
                {Object.values(filters).some(Boolean) 
                  ? 'Try adjusting your filters or search terms.'
                  : 'No betting opportunities are currently available. Please check back later.'
                }
              </p>
              {Object.values(filters).some(Boolean) && (
                <button onClick={clearFilters} className="btn btn-outline-primary">
                  Clear Filters
                </button>
              )}
            </div>
          ) : (
            <div id="opportunity-grid" className="opportunity-grid" role="list">
              {opportunities.map((opportunity, index) => (
                <BetCard 
                  key={opportunity.id || index} 
                  opportunity={opportunity} 
                  index={index} 
                />
              ))}
            </div>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="footer mt-5 py-3 bg-light">
        <div className="content-wrap">
          <div className="text-center">
            <small className="text-muted">
              Sports Betting +EV Analyzer v2.1.0 | 
              <span id="last-updated">Last updated: <span className="fw-bold">{formatLastUpdated(lastUpdated)}</span></span> |
              <a href="/education" className="text-muted text-decoration-none" title="Learn about sports betting basics">📚 Learn the Basics</a> |
              <a href="/disclaimer" className="text-muted text-decoration-none" title="Important legal disclaimer and risk disclosure">⚠️ Disclaimer</a>
            </small>
          </div>
        </div>
      </footer>
    </>
  );
};

export default DashboardPage; 