import React, { createContext, useState, useContext, useEffect, type ReactNode } from 'react';
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

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<UserWithRole | null>(null);
  const [session, setSession] = useState<AuthSession>(null);
  const [loading, setLoading] = useState(true);

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
          user_metadata: userWithRole.user_metadata
        });
        return userWithRole;
      } else {
        console.error('❌ Failed to fetch user role:', response.status, response.statusText);
        const responseText = await response.text();
        console.error('❌ Response body:', responseText);
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
    // Get initial session
    const getInitialSession = async () => {
      try {
        const session = await auth.getSession();
        setSession(session);
        
        if (session?.user) {
          const userWithRole = await fetchUserRole(session.user);
          setUser(userWithRole);
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
      
      if (session?.user) {
        const userWithRole = await fetchUserRole(session.user);
        setUser(userWithRole);
      } else {
        setUser(null);
      }
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

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
    loading,
    isAuthenticated: !!user,
    signIn,
    signUp,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}; 