import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoadingSpinner } from './common/LoadingSpinner';

interface PrivateRouteProps {
  children: React.ReactNode;
  requireRole?: 'basic' | 'premium' | 'admin';
  redirectTo?: string;
}

/**
 * PrivateRoute component for protecting authenticated pages
 * 
 * Features:
 * - Redirects unauthenticated users to login page
 * - Preserves intended destination for post-login redirect
 * - Supports role-based access control for premium features
 * - Shows loading spinner during authentication checks
 * - Graceful handling of authentication states
 */
export const PrivateRoute: React.FC<PrivateRouteProps> = ({ 
  children, 
  requireRole,
  redirectTo = '/login' 
}) => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    return (
      <Navigate 
        to={redirectTo} 
        state={{ from: location.pathname }} 
        replace 
      />
    );
  }

  // Check role-based access if required
  if (requireRole) {
    const userRole = user.user_metadata?.role;
    const subscriptionStatus = user.user_metadata?.subscription_status;

    // Check if user has required role and active subscription
    const hasRequiredRole = userRole === requireRole || 
                           (requireRole === 'basic' && userRole === 'premium') || // Premium includes basic
                           userRole === 'admin'; // Admin has access to everything

    const hasActiveSubscription = subscriptionStatus === 'active';

    if (!hasRequiredRole || !hasActiveSubscription) {
      // Redirect to pricing page for upgrade
      return <Navigate to="/pricing" state={{ requiredRole: requireRole }} replace />;
    }
  }

  // Render protected content
  return <>{children}</>;
};

/**
 * PublicRoute component for login/signup pages
 * Redirects authenticated users away from public-only pages
 */
interface PublicRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export const PublicRoute: React.FC<PublicRouteProps> = ({ 
  children, 
  redirectTo = '/' 
}) => {
  const { isAuthenticated, loading } = useAuth();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <LoadingSpinner size="lg" text="Loading..." />
      </div>
    );
  }

  // Redirect authenticated users away from login/signup
  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  // Render public content for unauthenticated users
  return <>{children}</>;
};