import { useOpportunities } from '../hooks/useOpportunities';
import { BetCard } from '../components/BetCard';

export const DashboardPage = () => {
  const {
    opportunities,
    loading,
    error,
    totalCount,
    showingCount,
    lastUpdate,
    searchTerm,
    setSearchTerm,
    refreshOpportunities
  } = useOpportunities();

  if (loading && opportunities.length === 0) {
    return (
      <div className="container mt-4">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Loading betting opportunities...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mt-4">
        <div className="alert alert-danger" role="alert">
          <h4 className="alert-heading">Error Loading Data</h4>
          <p>{error}</p>
          <button 
            className="btn btn-outline-danger"
            onClick={() => refreshOpportunities()}
          >
            <i className="fas fa-redo me-1"></i>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container-xxl mt-4">
      {/* Header Section */}
      <div className="row mb-4">
        <div className="col-12">
          <h1 className="h2 mb-0">
            <i className="fas fa-chart-line text-primary me-2"></i>
            Live Betting Opportunities
          </h1>
          <p className="text-muted">
            Real-time +EV analysis across multiple sportsbooks
          </p>
        </div>
      </div>



      {/* Search Section */}
      <div className="row mb-4">
        <div className="col-md-6">
          <div className="input-group">
            <span className="input-group-text">
              <i className="fas fa-search"></i>
            </span>
            <input
              type="text"
              className="form-control"
              placeholder="Search events, teams, or markets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button
                className="btn btn-outline-secondary"
                type="button"
                onClick={() => setSearchTerm('')}
              >
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Opportunities Grid */}
      <div className="row">
        {opportunities.length === 0 ? (
          <div className="col-12">
            <div className="text-center py-5">
              <i className="fas fa-search fa-3x text-muted mb-3"></i>
              <h4>No Opportunities Found</h4>
              <p className="text-muted">
                {searchTerm 
                  ? `No results found for "${searchTerm}". Try a different search term.`
                  : "No betting opportunities are currently available. Check back soon!"
                }
              </p>
            </div>
          </div>
        ) : (
          opportunities.map((opportunity, index) => (
            <div key={index} className="col-lg-6 col-xl-4 mb-4">
              <BetCard opportunity={opportunity} index={index} />
            </div>
          ))
        )}
      </div>

      {/* Loading indicator for refresh */}
      {loading && opportunities.length > 0 && (
        <div className="text-center mt-3">
          <div className="spinner-border spinner-border-sm text-primary" role="status">
            <span className="visually-hidden">Refreshing...</span>
          </div>
          <small className="text-muted ms-2">Refreshing data...</small>
        </div>
      )}
    </div>
  );
}; 