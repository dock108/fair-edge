import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Get the return URL from location state or search params, default to dashboard
  const searchParams = new URLSearchParams(location.search);
  const redirectTo = searchParams.get('redirect');
  const from = (location.state as any)?.from?.pathname || (redirectTo ? `/${redirectTo}` : '/');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await signIn(email, password);
      // Redirect to the page they were trying to access, or dashboard
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('Login error:', error);
      setError(error.message || 'Failed to sign in. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="main-container">
        <div className="auth-container">
          <div className="auth-card">
            <div className="auth-header">
              <h1 className="auth-title">Welcome Back</h1>
              <p className="auth-subtitle">Sign in to your FairEdge account</p>
            </div>

            <form onSubmit={handleSubmit} className="auth-form">
              {error && (
                <div className="error-message" style={{ 
                  backgroundColor: 'var(--error-50)', 
                  color: 'var(--error-700)', 
                  padding: 'var(--space-3)', 
                  borderRadius: 'var(--radius-md)', 
                  marginBottom: 'var(--space-4)',
                  border: '1px solid var(--error-200)'
                }}>
                  <i className="fas fa-exclamation-triangle" style={{ marginRight: 'var(--space-2)' }}></i>
                  {error}
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email" className="form-label">Email Address</label>
                <input
                  type="email"
                  id="email"
                  className="form-input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your email"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="password" className="form-label">Password</label>
                <input
                  type="password"
                  id="password"
                  className="form-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
              </div>

              <div className="form-options">
                <label className="checkbox-label">
                  <input type="checkbox" className="checkbox" />
                  <span className="checkbox-text">Remember me</span>
                </label>
                <a href="#" className="forgot-link">Forgot password?</a>
              </div>

              <button 
                type="submit" 
                className="btn btn-primary auth-button"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <i className="fas fa-spinner fa-spin"></i>
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </button>
            </form>

            <div className="auth-footer">
              <p>Don't have an account? <a href="/signup" className="auth-link">Sign up</a></p>
            </div>

            <div className="auth-divider">
              <span>or</span>
            </div>

            <div className="auth-note">
              <p>🎯 <strong>Demo Accounts:</strong> Use the test credentials provided in your setup, or create a new account to get started.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 