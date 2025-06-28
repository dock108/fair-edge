import React from 'react';
import { usePermissions, type FeatureScope } from '../hooks/usePermissions';
import { PremiumPrompt } from './PremiumPrompt';

interface FeatureGateProps {
  children: React.ReactNode;
  feature: FeatureScope;
  fallback?: React.ReactNode;
  featureName?: string;
  showPrompt?: boolean;
}

/**
 * FeatureGate component for role-based access control
 * 
 * Renders children only if the user has the required feature access.
 * Shows upgrade prompt or custom fallback for unauthorized users.
 */
export const FeatureGate: React.FC<FeatureGateProps> = ({
  children,
  feature,
  fallback,
  featureName,
  showPrompt = true
}) => {
  const { hasFeatureAccess, isAuthenticated, userRole, isSubscriptionActive } = usePermissions();

  // Allow access if user has the required feature access
  if (hasFeatureAccess(feature)) {
    return <>{children}</>;
  }

  // Custom fallback takes precedence over default prompt
  if (fallback) {
    return <>{fallback}</>;
  }

  // Don't show prompt if explicitly disabled
  if (!showPrompt) {
    return null;
  }

  // Show appropriate upgrade message based on user state
  if (!isAuthenticated) {
    return (
      <PremiumPrompt featureName={featureName}>
        Sign in to access {featureName || 'premium features'} and unlock advanced betting analytics.
      </PremiumPrompt>
    );
  }

  if (!isSubscriptionActive) {
    return (
      <PremiumPrompt featureName={featureName}>
        Upgrade your subscription to access {featureName || 'this feature'} and take your betting to the next level.
      </PremiumPrompt>
    );
  }

  // User is authenticated but doesn't have required tier
  if (feature === 'premium' && userRole === 'basic') {
    return (
      <PremiumPrompt featureName={featureName}>
        Upgrade to Premium to access {featureName || 'advanced features'} including player props, futures, and data export.
      </PremiumPrompt>
    );
  }

  if (feature === 'admin') {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 mb-2">
          <i className="fas fa-lock text-2xl"></i>
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Access Denied</h3>
        <p className="text-gray-600">This feature requires administrator privileges.</p>
      </div>
    );
  }

  // Default fallback
  return (
    <PremiumPrompt featureName={featureName}>
      Upgrade your plan to access {featureName || 'this feature'}.
    </PremiumPrompt>
  );
};