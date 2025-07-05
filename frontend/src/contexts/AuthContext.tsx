import React, { createContext, useState, useContext, useEffect, useCallback, type ReactNode } from 'react';
import type { User } from '@supabase/supabase-js';
import { auth } from '../lib/supabase';

// Define session type locally to avoid import issues
type AuthSession = {
  access_token: string;
  refresh_token: string;
  user: User;
} | null;

// Extended user type with role info from backend
type UserWithRole = User & {
  user_metadata: {
    role?: string;
    subscription_status?: string;
  };
};

interface AuthContextType {
  user: UserWithRole | null;
  session: AuthSession;
  accessToken: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, metadata?: any) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

// Constants for session management
const INACTIVITY_TIMEOUT = 48 * 60 * 60 * 1000; // 48 hours in milliseconds
const LAST_ACTIVE_KEY = 'lastActive';
const ACTIVITY_EVENTS = ['click', 'keypress', 'mousemove', 'scroll'];

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserWithRole | null>(null);
  const [session, setSession] = useState<AuthSession>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Activity tracking functions
  const updateLastActive = useCallback(() => {
    localStorage.setItem(LAST_ACTIVE_KEY, Date.now().toString());
  }, []);

  // Check for inactivity and auto-logout if needed
  const checkInactivity = useCallback(async () => {
    const lastActiveStr = localStorage.getItem(LAST_ACTIVE_KEY);
    if (lastActiveStr) {
      const lastActive = parseInt(lastActiveStr, 10);
      const timeSinceLastActive = Date.now() - lastActive;
      
      if (timeSinceLastActive >= INACTIVITY_TIMEOUT) {
        console.log('Session expired due to inactivity, logging out...');
        await auth.signOut();
        localStorage.removeItem(LAST_ACTIVE_KEY);
        return true; // Indicates logout occurred
      }
    }
    // Update activity timestamp since user just loaded/interacted with app
    updateLastActive();
    return false;
  }, [updateLastActive]);

  // Function to fetch user role from backend
  const fetchUserRole = async (supabaseUser: User): Promise<UserWithRole> => {
    try {
      const session = await auth.getSession();
      if (!session?.access_token) {
        console.log('No access token available');
        return supabaseUser as UserWithRole;
      }
      
      console.log('Fetching user role from backend...');
      const url = '/api/user-info'; // Proxy will route this to the backend
      console.log('🔗 Making request to:', url);
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });
      
      if (response.ok) {
        const userInfo = await response.json();
        console.log('✅ User role fetched from backend:', userInfo);
        
        // Enhanced validation of backend response
        if (!userInfo.role || userInfo.role === 'anonymous') {
          console.warn('⚠️ Backend returned invalid role:', userInfo.role);
          console.warn('⚠️ This might indicate the user is not found in backend database');
        }
        
        const userWithRole = {
          ...supabaseUser,
          user_metadata: {
            ...supabaseUser.user_metadata,
            role: userInfo.role,
            subscription_status: userInfo.subscription_status
          }
        };
        console.log('✅ Updated user object:', {
          email: userWithRole.email,
          role: userWithRole.user_metadata.role,
          subscription_status: userWithRole.user_metadata.subscription_status,
          user_metadata: userWithRole.user_metadata
        });
        return userWithRole;
      } else {
        console.error('❌ Failed to fetch user role:', response.status, response.statusText);
        const responseText = await response.text();
        console.error('❌ Response body:', responseText);
        console.error('❌ This suggests backend authentication or database issues');
      }
    } catch (error) {
      console.error('Error fetching user role:', error);
    }
    
    // Fallback to original user if API call fails
    console.log('⚠️ Falling back to original user (no role fetched)');
    const fallbackUser = supabaseUser as UserWithRole;
    console.log('⚠️ Fallback user:', {
      email: fallbackUser.email,
      role: fallbackUser.user_metadata?.role,
      user_metadata: fallbackUser.user_metadata
    });
    return fallbackUser;
  };

  useEffect(() => {
    // Get initial session with inactivity check
    const getInitialSession = async () => {
      try {
        // First check for inactivity before proceeding
        const wasLoggedOut = await checkInactivity();
        if (wasLoggedOut) {
          setLoading(false);
          return;
        }

        const session = await auth.getSession();
        setSession(session);
        setAccessToken(session?.access_token || null);
        
        if (session?.user) {
          const userWithRole = await fetchUserRole(session.user);
          setUser(userWithRole);
          updateLastActive(); // Update activity since user is actively using app
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Error getting initial session:', error);
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    // Listen for auth state changes
    const { data: { subscription } } = auth.onAuthStateChange(async (event, session) => {
      console.log('Auth state changed:', event, session?.user?.email);
      setSession(session);
      setAccessToken(session?.access_token || null);
      
      if (session?.user && (event === 'SIGNED_IN' || event === 'INITIAL_SESSION' || event === 'TOKEN_REFRESHED')) {
        const userWithRole = await fetchUserRole(session.user);
        setUser(userWithRole);
        updateLastActive(); // Update activity on any auth-confirming event
      } else if (event === 'SIGNED_OUT') {
        // Clear all auth state and user-specific data
        setUser(null);
        setAccessToken(null);
        localStorage.removeItem(LAST_ACTIVE_KEY);
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, [checkInactivity, updateLastActive]);

  // Set up activity tracking
  useEffect(() => {
    // Only track activity if user is logged in
    if (!user) return;

    // Throttle activity updates to avoid excessive localStorage writes
    let throttleTimer: NodeJS.Timeout | null = null;
    const throttledUpdateActivity = () => {
      if (throttleTimer) return;
      throttleTimer = setTimeout(() => {
        updateLastActive();
        throttleTimer = null;
      }, 30000); // Update at most once every 30 seconds
    };

    // Add event listeners for user activity
    ACTIVITY_EVENTS.forEach(event => {
      window.addEventListener(event, throttledUpdateActivity, { passive: true });
    });

    // Clean up on unmount
    return () => {
      ACTIVITY_EVENTS.forEach(event => {
        window.removeEventListener(event, throttledUpdateActivity);
      });
      if (throttleTimer) {
        clearTimeout(throttleTimer);
      }
    };
  }, [user, updateLastActive]);

  const signIn = async (email: string, password: string) => {
    setLoading(true);
    try {
      const { session, user } = await auth.signIn(email, password);
      setSession(session);
      
      if (user) {
        const userWithRole = await fetchUserRole(user);
        setUser(userWithRole);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Sign in error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signUp = async (email: string, password: string, metadata?: any) => {
    setLoading(true);
    try {
      const { session, user } = await auth.signUp(email, password, metadata);
      setSession(session);
      
      if (user) {
        const userWithRole = await fetchUserRole(user);
        setUser(userWithRole);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Sign up error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const signOut = async () => {
    setLoading(true);
    try {
      await auth.signOut();
      setSession(null);
      setUser(null);
    } catch (error) {
      console.error('Sign out error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    session,
    accessToken,
    loading,
    isAuthenticated: !!user,
    signIn,
    signUp,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 