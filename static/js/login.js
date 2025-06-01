/**
 * Login JavaScript for Supabase Authentication
 * Handles login form submission and JWT token storage
 */

(function() {
    'use strict';

    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeLogin();
        checkExistingSession();
    });

    /**
     * Initialize login form functionality
     */
    function initializeLogin() {
        const form = document.getElementById('login-form');
        const errorBox = document.getElementById('error-message');
        const loadingSpinner = document.getElementById('loading-spinner');
        const loginText = document.getElementById('login-text');

        if (!form) {
            console.error('Login form not found');
            return;
        }

        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Clear any previous errors
            hideError();
            
            // Show loading state
            showLoading();
            
            try {
                const email = form.email.value.trim();
                const password = form.password.value;

                // Validate inputs
                if (!email || !password) {
                    throw new Error('Please fill in all fields');
                }

                // Attempt to sign in with Supabase
                const { data, error } = await window.supabase.auth.signInWithPassword({
                    email: email,
                    password: password
                });

                if (error) {
                    throw new Error(error.message);
                }

                if (!data.session) {
                    throw new Error('Login failed - no session created');
                }

                // Store the JWT token
                const token = data.session.access_token;
                localStorage.setItem('sb_token', token);
                
                // Store user info for quick access
                if (data.user) {
                    localStorage.setItem('sb_user', JSON.stringify({
                        id: data.user.id,
                        email: data.user.email,
                        role: data.user.user_metadata?.role || 'free'
                    }));
                }

                // Show success and redirect
                showSuccess('Login successful! Redirecting...');
                
                // Brief delay for user feedback, then redirect
                setTimeout(() => {
                    window.location.href = '/dashboard';
                }, 1000);

            } catch (error) {
                console.error('Login error:', error);
                showError(error.message);
                hideLoading();
            }
        });

        /**
         * Show loading state
         */
        function showLoading() {
            loadingSpinner.style.display = 'inline-block';
            loginText.textContent = 'Signing in...';
            form.querySelector('button[type="submit"]').disabled = true;
        }

        /**
         * Hide loading state
         */
        function hideLoading() {
            loadingSpinner.style.display = 'none';
            loginText.textContent = 'Sign In';
            form.querySelector('button[type="submit"]').disabled = false;
        }

        /**
         * Show error message
         */
        function showError(message) {
            errorBox.textContent = message;
            errorBox.style.display = 'block';
            errorBox.style.backgroundColor = '#fee';
            errorBox.style.color = '#c33';
        }

        /**
         * Show success message
         */
        function showSuccess(message) {
            errorBox.textContent = message;
            errorBox.style.display = 'block';
            errorBox.style.backgroundColor = '#efe';
            errorBox.style.color = '#363';
        }

        /**
         * Hide error/success message
         */
        function hideError() {
            errorBox.style.display = 'none';
        }
    }

    /**
     * Check if user is already logged in
     */
    async function checkExistingSession() {
        try {
            // Check localStorage for existing token
            const existingToken = localStorage.getItem('sb_token');
            
            if (existingToken) {
                // Verify token with Supabase
                const { data: { session }, error } = await window.supabase.auth.getSession();
                
                if (session && !error) {
                    // User is already logged in, redirect to dashboard
                    console.log('User already logged in, redirecting...');
                    window.location.href = '/dashboard';
                    return;
                }
            }

            // Check for session from Supabase directly
            const { data: { session }, error } = await window.supabase.auth.getSession();
            
            if (session && !error) {
                // Update localStorage with fresh token
                localStorage.setItem('sb_token', session.access_token);
                
                if (session.user) {
                    localStorage.setItem('sb_user', JSON.stringify({
                        id: session.user.id,
                        email: session.user.email,
                        role: session.user.user_metadata?.role || 'free'
                    }));
                }
                
                // Redirect to dashboard
                window.location.href = '/dashboard';
            }
            
        } catch (error) {
            console.log('No existing session found:', error.message);
            // Continue with login form
        }
    }

    /**
     * Utility function to get stored user info
     */
    window.getCurrentUser = function() {
        try {
            const userStr = localStorage.getItem('sb_user');
            return userStr ? JSON.parse(userStr) : null;
        } catch (error) {
            console.error('Error parsing stored user data:', error);
            return null;
        }
    };

    /**
     * Utility function to get stored token
     */
    window.getAuthToken = function() {
        return localStorage.getItem('sb_token');
    };

    /**
     * Utility function to clear auth data
     */
    window.clearAuthData = function() {
        localStorage.removeItem('sb_token');
        localStorage.removeItem('sb_user');
    };

})(); 