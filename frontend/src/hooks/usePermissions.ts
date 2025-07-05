import { useAuth } from '../contexts/AuthContext';

export type UserRole = 'free' | 'basic' | 'premium' | 'admin';
export type FeatureScope = 'basic' | 'premium' | 'admin';

interface PermissionHook {
  userRole: UserRole;
  isAuthenticated: boolean;
  hasRole: (requiredRole: UserRole) => boolean;
  hasFeatureAccess: (feature: FeatureScope) => boolean;
  canAccessPremium: boolean;
  canExportData: boolean;
  canAccessAdmin: boolean;
  isSubscriptionActive: boolean;
}

/**
 * Custom hook for role-based access control
 * 
 * Provides utilities for checking user permissions and feature access
 * based on their subscription tier and authentication status.
 */
export const usePermissions = (): PermissionHook => {
  const { user, isAuthenticated } = useAuth();
  
  const userRole: UserRole = (user?.user_metadata?.role as UserRole) || 'free';
  const subscriptionStatus = user?.user_metadata?.subscription_status || 'none';
  const isSubscriptionActive = subscriptionStatus === 'active' || userRole === 'admin';

  // Debug logging to help identify the issue
  if (user && import.meta.env.DEV) {
    console.log('🔍 usePermissions debug:', {
      userEmail: user.email,
      rawRole: user?.user_metadata?.role,
      finalUserRole: userRole,
      subscriptionStatus,
      isSubscriptionActive,
      userMetadata: user.user_metadata
    });
  }

  /**
   * Check if user has a specific role or higher
   * Role hierarchy: free < basic < premium < admin
   */
  const hasRole = (requiredRole: UserRole): boolean => {
    if (!isAuthenticated) return requiredRole === 'free';
    
    const roleHierarchy: Record<UserRole, number> = {
      free: 0,
      basic: 1,
      premium: 2,
      admin: 3
    };
    
    const userLevel = roleHierarchy[userRole] || 0;
    const requiredLevel = roleHierarchy[requiredRole] || 0;
    
    return userLevel >= requiredLevel;
  };

  /**
   * Check if user has access to a specific feature scope
   */
  const hasFeatureAccess = (feature: FeatureScope): boolean => {
    switch (feature) {
      case 'basic':
        return isAuthenticated && (hasRole('basic') || hasRole('premium') || hasRole('admin')) && isSubscriptionActive;
      case 'premium':
        return isAuthenticated && (hasRole('premium') || hasRole('admin')) && isSubscriptionActive;
      case 'admin':
        return isAuthenticated && hasRole('admin');
      default:
        return false;
    }
  };

  return {
    userRole,
    isAuthenticated,
    hasRole,
    hasFeatureAccess,
    canAccessPremium: hasFeatureAccess('basic'),
    canExportData: hasFeatureAccess('premium'),
    canAccessAdmin: hasFeatureAccess('admin'),
    isSubscriptionActive
  };
};