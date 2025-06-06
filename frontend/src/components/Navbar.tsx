import { Link } from 'react-router-dom';
import type { NavbarProps } from '../types';

export const Navbar = ({ user, onLogout }: NavbarProps) => {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
      <div className="container">
        <Link className="navbar-brand" to="/">
          <i className="fas fa-chart-line me-2"></i>
          Sports +EV Analyzer
        </Link>

        <button 
          className="navbar-toggler" 
          type="button" 
          data-bs-toggle="collapse" 
          data-bs-target="#navbarNav"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        <div className="collapse navbar-collapse" id="navbarNav">
          <ul className="navbar-nav me-auto">
            <li className="nav-item">
              <Link className="nav-link" to="/">
                <i className="fas fa-tachometer-alt me-1"></i>
                Dashboard
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/education">
                <i className="fas fa-graduation-cap me-1"></i>
                Education
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/pricing">
                <i className="fas fa-tag me-1"></i>
                Pricing
              </Link>
            </li>
            <li className="nav-item">
              <Link className="nav-link" to="/disclaimer">
                <i className="fas fa-exclamation-triangle me-1"></i>
                Disclaimer
              </Link>
            </li>
          </ul>

          <ul className="navbar-nav">
            {user ? (
              <>
                <li className="nav-item">
                  <span className="navbar-text me-3">
                    <i className="fas fa-user me-1"></i>
                    {user.email}
                    {user.role === 'admin' && (
                      <span className="badge bg-danger ms-1">Admin</span>
                    )}
                    {user.role === 'subscriber' && (
                      <span className="badge bg-success ms-1">Pro</span>
                    )}
                  </span>
                </li>
                <li className="nav-item">
                  <button 
                    className="btn btn-outline-light btn-sm"
                    onClick={onLogout}
                  >
                    <i className="fas fa-sign-out-alt me-1"></i>
                    Logout
                  </button>
                </li>
              </>
            ) : (
              <li className="nav-item">
                <Link className="btn btn-outline-light btn-sm" to="/login">
                  <i className="fas fa-sign-in-alt me-1"></i>
                  Login
                </Link>
              </li>
            )}
          </ul>
        </div>
      </div>
    </nav>
  );
}; 