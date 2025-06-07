import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, isAuthenticated, signOut, loading } = useAuth();

  const handleLogout = async () => {
    try {
      await signOut();
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
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
            to="/education" 
            className={`nav-link ${location.pathname === '/education' ? 'active' : ''}`}
          >
            Education
          </Link>
          <Link 
            to="/pricing" 
            className={`nav-link ${location.pathname === '/pricing' ? 'active' : ''}`}
          >
            Pricing
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
            <div className="user-menu">
              <span className="user-email">{user.email}</span>
              <button onClick={handleLogout} className="btn btn-outline">
                <i className="fas fa-sign-out-alt" style={{ marginRight: 'var(--space-2)' }}></i>
                Logout
              </button>
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