/**
 * Helper functions for testing authentication improvements
 * Use these in the browser console for testing
 */

// Get the Supabase project reference from environment
const getProjectRef = () => {
  const url = import.meta.env.VITE_SUPABASE_URL;
  if (!url) return null;
  const match = url.match(/https:\/\/([^.]+)\.supabase\.co/);
  return match ? match[1] : null;
};

export const authTestHelpers = {
  // Check current auth state
  checkAuthState: () => {
    const projectRef = getProjectRef();
    if (!projectRef) {
      console.error('Could not determine Supabase project reference');
      return;
    }
    
    const tokenKey = `sb-${projectRef}-auth-token`;
    const authData = localStorage.getItem(tokenKey);
    const lastActive = localStorage.getItem('lastActive');
    
    if (!authData) {
      console.log('❌ No auth token found - user is logged out');
      return;
    }
    
    const parsed = JSON.parse(authData);
    const now = Math.floor(Date.now() / 1000);
    const expiresIn = parsed.expires_at - now;
    
    console.log('🔐 Auth State:');
    console.log('- User:', parsed.user?.email);
    console.log('- Token expires in:', Math.floor(expiresIn / 60), 'minutes');
    console.log('- Refresh token:', parsed.refresh_token ? '✅ Present' : '❌ Missing');
    
    if (lastActive) {
      const lastActiveDate = new Date(parseInt(lastActive));
      const inactiveHours = (Date.now() - parseInt(lastActive)) / (1000 * 60 * 60);
      console.log('- Last active:', lastActiveDate.toLocaleString());
      console.log('- Inactive for:', inactiveHours.toFixed(1), 'hours');
    }
  },

  // Force token expiry for testing
  forceTokenExpiry: () => {
    const projectRef = getProjectRef();
    if (!projectRef) return;
    
    const tokenKey = `sb-${projectRef}-auth-token`;
    const authData = localStorage.getItem(tokenKey);
    
    if (!authData) {
      console.error('No auth token found');
      return;
    }
    
    const parsed = JSON.parse(authData);
    parsed.expires_at = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago
    localStorage.setItem(tokenKey, JSON.stringify(parsed));
    
    console.log('✅ Token expiry forced - next API call should trigger refresh');
  },

  // Corrupt access token to test 401 handling
  corruptAccessToken: () => {
    const projectRef = getProjectRef();
    if (!projectRef) return;
    
    const tokenKey = `sb-${projectRef}-auth-token`;
    const authData = localStorage.getItem(tokenKey);
    
    if (!authData) {
      console.error('No auth token found');
      return;
    }
    
    const parsed = JSON.parse(authData);
    parsed.access_token = 'corrupted-token-for-testing';
    localStorage.setItem(tokenKey, JSON.stringify(parsed));
    
    console.log('✅ Access token corrupted - next API call should fail with 401');
  },

  // Simulate old activity
  simulateInactivity: (hours: number) => {
    const oldTime = Date.now() - (hours * 60 * 60 * 1000);
    localStorage.setItem('lastActive', oldTime.toString());
    console.log(`✅ Set last active to ${hours} hours ago`);
    console.log('Reload the page to trigger inactivity check');
  },

  // Clear all auth data
  clearAuthData: () => {
    const projectRef = getProjectRef();
    if (!projectRef) return;
    
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith(`sb-${projectRef}-`) || key === 'lastActive') {
        localStorage.removeItem(key);
      }
    });
    
    console.log('✅ All auth data cleared');
  },

  // Monitor auth events
  monitorAuthEvents: () => {
    console.log('📡 Monitoring auth events (activity will be logged here)...');
    
    // Monitor localStorage changes
    const originalSetItem = localStorage.setItem;
    localStorage.setItem = function(key: string, value: string) {
      if (key === 'lastActive') {
        console.log('⏰ Activity tracked:', new Date().toLocaleTimeString());
      }
      originalSetItem.apply(this, [key, value]);
    };
    
    // Monitor network requests
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name.includes('/auth/') || entry.name.includes('token')) {
          console.log('🔄 Auth request:', entry.name);
        }
      }
    });
    observer.observe({ entryTypes: ['resource'] });
    
    console.log('To stop monitoring, refresh the page');
  }
};

// Make available in browser console
if (typeof window !== 'undefined') {
  (window as any).authTest = authTestHelpers;
  console.log('🧪 Auth test helpers loaded! Use window.authTest.* in console');
}