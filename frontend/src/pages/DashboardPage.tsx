import { useOpportunities } from '../hooks/useOpportunities';
import { BetCard } from '../components/BetCard';
import { useAuth } from '../contexts/AuthContext';
import PremiumPrompt from '../components/PremiumPrompt';
import { useEffect } from 'react';

export const DashboardPage = () => {
  const {
    opportunities,
    loading,
    error,
    searchTerm,
    setSearchTerm,
    refreshOpportunities
  } = useOpportunities();
  
  const { user, isAuthenticated, loading: authLoading } = useAuth();

  // Debug: Log user role information
  useEffect(() => {
    console.log('DashboardPage - User debug info:', {
      isAuthenticated,
      authLoading,
      user: user ? {
        email: user.email,
        role: user.user_metadata?.role,
        user_metadata: user.user_metadata
      } : null
    });
  }, [user, isAuthenticated, authLoading]);

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
        {/* Admin Badge - Positioned Absolutely */}
        {isAuthenticated && user?.user_metadata?.role === 'admin' && (
          <div style={{ 
            position: 'absolute',
            top: '0',
            right: '0',
            background: 'var(--success-50)',
            border: '1px solid var(--success-200)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-2) var(--space-3)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)'
          }}>
            <i className="fas fa-crown" 
               style={{ color: 'var(--success-600)' }}></i>
            <span style={{ 
              fontWeight: '500', 
              color: 'var(--success-700)' 
            }}>
              Admin
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
        
        {/* Access Level Banner */}
        {!isAuthenticated && (
          <div style={{ 
            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3)',
            marginTop: 'var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <strong style={{ color: '#d97706' }}>
                <i className="fas fa-eye" style={{ marginRight: 'var(--space-2)' }}></i>
                                    Preview Mode: Viewing 10 real sample opportunities
              </strong>
              <span style={{ color: '#92400e', marginLeft: 'var(--space-2)' }}>
                Sign up to see profitable opportunities!
              </span>
            </div>
            <a href="/pricing" className="btn btn-sm btn-primary" style={{ textDecoration: 'none' }}>
              Get Started
            </a>
          </div>
        )}
        {/* Role-specific upgrade messages - only show when not loading and user role is determined */}
        {!authLoading && isAuthenticated && user?.user_metadata?.role === 'free' && (
          <div style={{ 
            background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(251, 191, 36, 0.1) 100%)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3)',
            marginTop: 'var(--space-4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <strong style={{ color: '#d97706' }}>
                <i className="fas fa-exclamation-triangle" style={{ marginRight: 'var(--space-2)' }}></i>
                Free Tier: Showing 10 unprofitable bets only (-2% EV or worse)
              </strong>
              <span style={{ color: '#92400e', marginLeft: 'var(--space-2)' }}>
                Upgrade to Basic ($3.99) to see profitable opportunities!
              </span>
            </div>
            <a href="/pricing" className="btn btn-sm btn-primary" style={{ textDecoration: 'none' }}>
              Upgrade
            </a>
          </div>
        )}
        {/* Basic users get no upgrade messages - clean experience like premium users */}
      </div>

      {/* Search Section - Hidden for unauthenticated and free users */}
      {!authLoading && isAuthenticated && user?.user_metadata?.role !== 'free' && (
        <div className="row mb-4 justify-content-center">
          <div className="col-md-6 col-lg-5 col-xl-4">
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
      )}

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
          
          {/* Upsell for Unauthenticated Users */}
          {!isAuthenticated && (
            <PremiumPrompt featureName="profitable betting opportunities">
              <strong>These are just the unprofitable bets!</strong>
              <br />
              Sign up for Basic ($3.99) to see profitable main lines, or Premium ($9.99) for complete market coverage including player props and alternate lines.
            </PremiumPrompt>
          )}
          
          {/* Limited Content Notice for Free Users */}
          {!authLoading && isAuthenticated && user?.user_metadata?.role === 'free' && opportunities.length > 0 && (
            <div style={{
              background: 'rgba(245, 158, 11, 0.05)',
              border: '1px solid rgba(245, 158, 11, 0.2)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4)',
              textAlign: 'center',
              marginTop: 'var(--space-6)'
            }}>
              <h4 style={{ color: '#d97706', marginBottom: 'var(--space-3)' }}>
                <i className="fas fa-exclamation-triangle" style={{ marginRight: 'var(--space-2)' }}></i>
                You're Only Seeing Losing Bets!
              </h4>
              <p style={{ color: '#92400e', marginBottom: 'var(--space-4)' }}>
                These 10 opportunities have <strong>-2% EV or worse</strong> - they're designed to lose money. Upgrade to see profitable opportunities:
              </p>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                gap: 'var(--space-4)',
                marginBottom: 'var(--space-4)'
              }}>
                <div style={{ 
                  background: 'rgba(59, 130, 246, 0.1)', 
                  padding: 'var(--space-3)', 
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(59, 130, 246, 0.2)'
                }}>
                  <h5 style={{ color: '#2563eb', marginBottom: 'var(--space-2)' }}>
                    <i className="fas fa-chart-line" style={{ marginRight: 'var(--space-2)' }}></i>
                    Basic - $3.99/month
                  </h5>
                  <p style={{ color: '#1e40af', fontSize: '0.9rem', margin: 0 }}>
                    Unlock <strong>positive EV main lines</strong> and start making profitable bets
                  </p>
                </div>
                <div style={{ 
                  background: 'rgba(245, 158, 11, 0.1)', 
                  padding: 'var(--space-3)', 
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid rgba(245, 158, 11, 0.2)'
                }}>
                  <h5 style={{ color: '#d97706', marginBottom: 'var(--space-2)' }}>
                    <i className="fas fa-crown" style={{ marginRight: 'var(--space-2)' }}></i>
                    Premium - $9.99/month
                  </h5>
                  <p style={{ color: '#92400e', fontSize: '0.9rem', margin: 0 }}>
                    Get <strong>everything + player props & alternate lines</strong> for maximum opportunities
                  </p>
                </div>
              </div>
              <a href="/pricing" className="btn btn-primary" style={{ textDecoration: 'none' }}>
                <i className="fas fa-arrow-up" style={{ marginRight: 'var(--space-2)' }}></i>
                Start Making Money
              </a>
            </div>
          )}

          {/* Basic users get no upsell messages - clean experience like premium users */}
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