import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/apiService';

export const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, signOut, loading } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [managingBilling, setManagingBilling] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const userRole = user?.user_metadata?.role;
  const subscriptionStatus = user?.user_metadata?.subscription_status;
  const hasActiveSubscription = (userRole === 'basic' || userRole === 'premium') && subscriptionStatus === 'active';

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    if (showUserMenu) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [showUserMenu]);

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleManageBilling = async () => {
    if (!hasActiveSubscription) {
      navigate('/pricing');
      return;
    }

    setManagingBilling(true);
    try {
      const response = await apiService.createPortalSession();
      window.location.href = response.url;
    } catch (error) {
      console.error('Failed to open billing portal:', error);
      alert('Unable to access billing portal. Please contact support.');
    } finally {
      setManagingBilling(false);
    }
  };

  return (
    <header className="site-header">
      <nav className="header-wrap">
        <div className="header-brand">
          <Link to="/" className="brand-link">
            <img src="/icons/fairedge_logo_64.png" alt="FairEdge logo" className="brand-logo" />
            <span className="brand-text">FairEdge</span>
          </Link>
        </div>
        
        <div className="header-nav">
          <Link 
            to="/" 
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Dashboard
          </Link>
          <Link 
            to="/pricing" 
            className={`nav-link ${location.pathname === '/pricing' ? 'active' : ''}`}
          >
            Pricing
          </Link>
          <Link 
            to="/education" 
            className={`nav-link ${location.pathname === '/education' ? 'active' : ''}`}
          >
            Education
          </Link>
          <Link 
            to="/disclaimer" 
            className={`nav-link ${location.pathname === '/disclaimer' ? 'active' : ''}`}
          >
            Disclaimer
          </Link>
        </div>

        <div className="header-actions">
          {loading ? (
            <div className="auth-loading">
              <i className="fas fa-spinner fa-spin"></i>
            </div>
          ) : isAuthenticated && user ? (
            <div className="user-menu-container" ref={menuRef}>
              <button 
                className="user-menu-trigger"
                onClick={() => setShowUserMenu(!showUserMenu)}
              >
                <span className="user-email">{user.email}</span>
                <i className={`fas fa-chevron-${showUserMenu ? 'up' : 'down'}`}></i>
              </button>
              
              {showUserMenu && (
                <div className="user-menu-dropdown">
                  <div className="user-menu-header">
                    <div className="user-info">
                      <strong>{user.email}</strong>
                      <span className="user-plan">
                        {userRole === 'basic' ? '💰 Basic Plan' : 
                         userRole === 'premium' ? '🚀 Premium Plan' : 
                         '🆓 Free Account'}
                      </span>
                    </div>
                  </div>
                  
                  <div className="user-menu-items">
                    <button 
                      onClick={handleManageBilling}
                      className="user-menu-item"
                      disabled={managingBilling}
                    >
                      <i className="fas fa-credit-card"></i>
                      {managingBilling ? (
                        <>
                          <i className="fas fa-spinner fa-spin"></i>
                          Opening...
                        </>
                      ) : hasActiveSubscription ? (
                        'Manage Subscription'
                      ) : (
                        'Upgrade Account'
                      )}
                    </button>
                    
                    <button onClick={handleLogout} className="user-menu-item logout">
                      <i className="fas fa-sign-out-alt"></i>
                      Logout
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn btn-outline">Login</Link>
              <Link to="/signup" className="btn btn-primary">Sign Up</Link>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}; 