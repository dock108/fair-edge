import type { User } from '@supabase/supabase-js';

// User permission utility functions
export const permissions = {
  // Check if user can access premium features (props, alt lines, etc.)
  canAccessPremiumFeatures(user: User | null): boolean {
    if (!user) return false;

    // Admin users have access to everything
    if (user.user_metadata?.role === 'admin') return true;

    // Premium subscribers have access to all features
    if (user.user_metadata?.role === 'premium' || user.user_metadata?.role === 'subscriber') {
      return true;
    }

    return false;
  },

  // Check if user can access basic features (positive EV main lines)
  canAccessBasicFeatures(user: User | null): boolean {
    if (!user) return false;

    // Admin users have access to everything
    if (user.user_metadata?.role === 'admin') return true;

    // Basic and premium subscribers have access to positive EV
    if (user.user_metadata?.role === 'basic' || user.user_metadata?.role === 'premium' || user.user_metadata?.role === 'subscriber') {
      return true;
    }

    return false;
  },

  // Check if user can access admin features
  canAccessAdminFeatures(user: User | null): boolean {
    if (!user) return false;
    return user.user_metadata?.role === 'admin';
  },

  // Check if user is on free tier
  isFreeTier(user: User | null): boolean {
    if (!user) return true;
    return user.user_metadata?.role === 'free' || !user.user_metadata?.role;
  },

  // Get user role display name
  getUserRoleDisplay(user: User | null): string {
    if (!user) return 'Free';

    const role = user.user_metadata?.role;
    switch (role) {
      case 'admin':
        return 'Admin';
      case 'premium':
      case 'subscriber': // backward compatibility
        return 'Premium';
      case 'basic':
        return 'Basic';
      case 'free':
      default:
        return 'Free';
    }
  },

  // Check if user can see specific bet types
  canSeeBetType(user: User | null, betType: string): boolean {
    // Free users can only see main lines
    const mainLines = ['moneyline', 'spread', 'total', 'over', 'under'];

    if (this.isFreeTier(user)) {
      return mainLines.some(mainLine =>
        betType.toLowerCase().includes(mainLine)
      );
    }

    // Basic users can see all main lines
    if (user?.user_metadata?.role === 'basic') {
      return mainLines.some(mainLine =>
        betType.toLowerCase().includes(mainLine)
      );
    }

    // Premium and admin users can see everything
    return this.canAccessPremiumFeatures(user);
  },

  // Check if user can see positive EV opportunities
  canSeePositiveEV(user: User | null): boolean {
    return this.canAccessBasicFeatures(user);
  },

  // Check EV threshold for filtering opportunities
  getEVThreshold(user: User | null): number {
    // Free users only see -2% EV or worse
    if (this.isFreeTier(user)) {
      return -2.0;
    }

    // Paid users see all EV values
    return -Infinity;
  }
};

export default permissions;
