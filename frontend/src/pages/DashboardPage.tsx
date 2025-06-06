import { useOpportunities } from '../hooks/useOpportunities';
import { BetCard } from '../components/BetCard';
import { useAuth } from '../contexts/AuthContext';
import { permissions } from '../utils/permissions';
import PremiumPrompt from '../components/PremiumPrompt';

export const DashboardPage = () => {
  const {
    opportunities,
    loading,
    error,
    searchTerm,
    setSearchTerm,
    refreshOpportunities
  } = useOpportunities();
  
  const { user, isAuthenticated } = useAuth();
  const canAccessPremium = permissions.canAccessPremiumFeatures(user);
  const userRole = permissions.getUserRoleDisplay(user);

  if (loading && opportunities.length === 0) {
    return (
      <div className="main-container">
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
      <div className="main-container">
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
    <div className="main-container">
      {/* Header Section */}
      <div className="dashboard-header">
        {/* User Badge - Positioned Absolutely */}
        {isAuthenticated && (
          <div style={{ 
            position: 'absolute',
            top: '0',
            right: '0',
            background: canAccessPremium ? 'var(--success-50)' : 'var(--grey-50)',
            border: `1px solid ${canAccessPremium ? 'var(--success-200)' : 'var(--grey-200)'}`,
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-3)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)'
          }}>
            <i className={`fas ${canAccessPremium ? 'fa-crown' : 'fa-user'}`} 
               style={{ color: canAccessPremium ? 'var(--success-600)' : 'var(--grey-600)' }}></i>
            <span style={{ 
              fontWeight: '500', 
              color: canAccessPremium ? 'var(--success-700)' : 'var(--grey-700)' 
            }}>
              {userRole} User
            </span>
          </div>
        )}
        
        {/* Centered Title and Subtitle */}
        <div style={{ textAlign: 'center', marginBottom: 'var(--space-4)' }}>
          <h1 className="dashboard-title">
            <i className="fas fa-chart-line"></i>
            Live Betting Opportunities
          </h1>
          <p className="dashboard-subtitle">
            Real-time +EV analysis across multiple sportsbooks
          </p>
        </div>
        
        {/* Centered Optimization Info */}
        <div style={{ textAlign: 'center' }}>
          <div className="optimization-info">
            <i className="fas fa-info-circle"></i>
            <span>All P2P posting recommendations are optimized for 2.5% target EV after exchange fees</span>
          </div>
        </div>
        
        {/* Premium Access Banner for Free Users */}
        {isAuthenticated && !canAccessPremium && (
          <div style={{ 
            background: 'linear-gradient(135deg, var(--brand-50) 0%, var(--brand-100) 100%)',
            border: '1px solid var(--brand-200)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3)',
            marginTop: 'var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <strong style={{ color: 'var(--brand-700)' }}>
                <i className="fas fa-star" style={{ marginRight: 'var(--space-2)' }}></i>
                You're viewing main lines only
              </strong>
              <span style={{ color: 'var(--brand-600)', marginLeft: 'var(--space-2)' }}>
                Upgrade to see player props, alternate lines, and more!
              </span>
            </div>
            <a href="/pricing" className="btn btn-sm btn-primary" style={{ textDecoration: 'none' }}>
              Upgrade
            </a>
          </div>
        )}
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
      {opportunities.length === 0 ? (
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
      ) : (
        <>
          <div className="dashboard-grid">
            {opportunities.map((opportunity, index) => (
              <BetCard key={index} opportunity={opportunity} index={index} />
            ))}
          </div>
          
          {/* Premium Upsell for Free Users */}
          {!isAuthenticated && (
            <PremiumPrompt featureName="premium betting opportunities">
              <strong>See player props, alternate lines, and live betting opportunities!</strong>
              <br />
              Join thousands of bettors finding profitable edges with our premium analysis.
            </PremiumPrompt>
          )}
          
          {/* Limited Content Notice for Authenticated Free Users */}
          {isAuthenticated && !canAccessPremium && opportunities.length > 0 && (
            <div style={{
              background: 'var(--grey-50)',
              border: '1px solid var(--grey-200)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              textAlign: 'center',
              marginTop: 'var(--space-6)'
            }}>
              <h4 style={{ color: 'var(--grey-700)', marginBottom: 'var(--space-3)' }}>
                <i className="fas fa-lock" style={{ marginRight: 'var(--space-2)' }}></i>
                More Opportunities Available
              </h4>
              <p style={{ color: 'var(--grey-600)', marginBottom: 'var(--space-4)' }}>
                You're seeing main lines only. Premium users have access to <strong>3x more opportunities</strong> including:
              </p>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
                gap: 'var(--space-3)',
                marginBottom: 'var(--space-4)'
              }}>
                <div>
                  <i className="fas fa-basketball-ball" style={{ color: 'var(--brand-500)', marginRight: 'var(--space-2)' }}></i>
                  Player Props
                </div>
                <div>
                  <i className="fas fa-chart-line" style={{ color: 'var(--brand-500)', marginRight: 'var(--space-2)' }}></i>
                  Alternate Lines
                </div>
                <div>
                  <i className="fas fa-clock" style={{ color: 'var(--brand-500)', marginRight: 'var(--space-2)' }}></i>
                  Live Betting
                </div>
                <div>
                  <i className="fas fa-trophy" style={{ color: 'var(--brand-500)', marginRight: 'var(--space-2)' }}></i>
                  Futures & Specials
                </div>
              </div>
              <a href="/pricing" className="btn btn-primary" style={{ textDecoration: 'none' }}>
                <i className="fas fa-star" style={{ marginRight: 'var(--space-2)' }}></i>
                Unlock All Opportunities
              </a>
            </div>
          )}
        </>
      )}

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