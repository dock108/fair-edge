import React from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import apiService from '../services/api';

const Navbar: React.FC = () => {
  const { user, isAdmin, isSubscriber, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleUpgrade = async () => {
    try {
      if (!user) {
        navigate('/login', { state: { intent: 'upgrade' } });
        return;
      }

      if (isSubscriber) {
        alert('You are already a Premium subscriber!');
        return;
      }

      const { checkout_url } = await apiService.createCheckoutSession();
      window.location.href = checkout_url;
    } catch (error) {
      console.error('Upgrade failed:', error);
      alert('Failed to start upgrade process. Please try again.');
    }
  };

  const handleManageBilling = async () => {
    try {
      const { portal_url } = await apiService.manageBilling();
      window.location.href = portal_url;
    } catch (error) {
      console.error('Manage billing failed:', error);
      alert('Failed to open billing portal. Please try again.');
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-light bg-light">
      <div className="content-wrap d-flex justify-content-between align-items-center">
        <div className="navbar-nav">
          <NavLink 
            to="/" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <i className="fas fa-home me-1"></i> Dashboard
          </NavLink>
          <NavLink 
            to="/education" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <i className="fas fa-graduation-cap me-1"></i> Education
          </NavLink>
          <NavLink 
            to="/pricing" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <i className="fas fa-tags me-1"></i> Pricing
          </NavLink>
          <NavLink 
            to="/disclaimer" 
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <i className="fas fa-exclamation-triangle me-1"></i> Disclaimer
          </NavLink>
          {isAdmin && (
            <NavLink 
              to="/admin" 
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <i className="fas fa-shield-alt me-1"></i> Admin
            </NavLink>
          )}
        </div>
        
        <div className="d-flex align-items-center gap-2">
          {/* Authentication status */}
          <div id="auth-status">
            {user ? (
              <div className="d-flex align-items-center gap-2">
                <Link to="/account" className="nav-link">
                  <i className="fas fa-user me-1"></i> My Account
                </Link>
                <button 
                  onClick={handleLogout}
                  className="btn btn-outline-secondary btn-sm"
                >
                  <i className="fas fa-sign-out-alt me-1"></i> Logout
                </button>
              </div>
            ) : (
              <Link to="/login" className="nav-link">
                <i className="fas fa-sign-in-alt me-1"></i> Login
              </Link>
            )}
          </div>

          {/* Admin Badge */}
          {isAdmin && (
            <span className="badge bg-danger rounded-pill">
              <i className="fas fa-shield-alt me-1"></i>Admin
            </span>
          )}
          
          {/* Manage Billing Button for Subscribers */}
          {isSubscriber && (
            <button 
              onClick={handleManageBilling}
              className="btn btn-outline-primary btn-sm"
            >
              <i className="fas fa-credit-card me-1"></i>
              Manage billing
            </button>
          )}
          
          {/* Upgrade CTA for free users */}
          {user && !isSubscriber && (
            <button 
              onClick={handleUpgrade}
              className="btn btn-warning btn-sm px-3 py-1 rounded-pill fw-bold"
              style={{ boxShadow: '0 2px 4px rgba(255,193,7,0.3)' }}
            >
              <i className="fas fa-star me-1"></i> Upgrade
            </button>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 