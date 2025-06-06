import type { User } from '@supabase/supabase-js';

// User permission utility functions
export const permissions = {
  // Check if user can access premium features (props, alt lines, etc.)
  canAccessPremiumFeatures(user: User | null): boolean {
    if (!user) return false;
    
    // Admin users have access to everything
    if (user.user_metadata?.role === 'admin') return true;
    
    // Subscribers with active subscription
    if (user.user_metadata?.role === 'subscriber') {
      // You might want to check subscription_status here too
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
      case 'subscriber':
        return 'Premium';
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
    
    // Premium and admin users can see everything
    return this.canAccessPremiumFeatures(user);
  }
};

export default permissions; 
 
 