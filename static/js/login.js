/**
 * Login JavaScript for Supabase Authentication
 * Handles login form submission and secure session creation
 * Production version uses httpOnly cookies instead of localStorage
 */

(function() {
    'use strict';

    // Configuration
    const USE_SECURE_COOKIES = true; // Set to true for production cookie-based auth

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

                // Handle authentication based on configuration
                if (USE_SECURE_COOKIES) {
                    // Production: Use secure session cookies
                    await createSecureSession(data);
                } else {
                    // Development: Use localStorage
                    await createLocalStorageSession(data);
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
         * Create secure session using httpOnly cookies
         */
        async function createSecureSession(authData) {
            try {
                const sessionResponse = await fetch('/api/session', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include', // Important for cookies
                    body: JSON.stringify({
                        access_token: authData.session.access_token,
                        user_data: {
                            id: authData.user.id,
                            email: authData.user.email,
                            role: authData.user.user_metadata?.role || 'free'
                        }
                    })
                });

                if (!sessionResponse.ok) {
                    const errorData = await sessionResponse.json();
                    throw new Error(`Session creation failed: ${errorData.detail || 'Unknown error'}`);
                }

                const sessionData = await sessionResponse.json();
                
                // Store CSRF token for API calls (readable by JS)
                if (sessionData.csrf_token) {
                    // The CSRF token is automatically set as a cookie by the server
                    // and also returned in the response for immediate use
                    window.csrfToken = sessionData.csrf_token;
                }

                console.log('Secure session created successfully');
                
            } catch (error) {
                console.error('Secure session creation failed:', error);
                throw new Error('Failed to create secure session');
            }
        }

        /**
         * Create session using localStorage (development fallback)
         */
        async function createLocalStorageSession(authData) {
            // Store the JWT token
            const token = authData.session.access_token;
            localStorage.setItem('sb_token', token);
            
            // Store user info for quick access
            if (authData.user) {
                localStorage.setItem('sb_user', JSON.stringify({
                    id: authData.user.id,
                    email: authData.user.email,
                    role: authData.user.user_metadata?.role || 'free'
                }));
            }

            console.log('localStorage session created');
        }

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
            if (USE_SECURE_COOKIES) {
                // Check for existing session via cookie-based endpoint
                const response = await fetch('/api/session/user', {
                    credentials: 'include'
                });
                
                if (response.ok) {
                    const userData = await response.json();
                    console.log('User already logged in:', userData.email);
                    window.location.href = '/dashboard';
                    return;
                }
            } else {
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
            }
            
        } catch (error) {
            console.log('No existing session found:', error.message);
            // Continue with login form
        }
    }

    /**
     * Utility function to get CSRF token from cookie
     */
    window.getCSRFToken = function() {
        if (USE_SECURE_COOKIES) {
            // Extract CSRF token from cookie
            const name = 'csrf_token=';
            const decodedCookie = decodeURIComponent(document.cookie);
            const cookieArray = decodedCookie.split(';');
            
            for (let i = 0; i < cookieArray.length; i++) {
                let cookie = cookieArray[i];
                while (cookie.charAt(0) === ' ') {
                    cookie = cookie.substring(1);
                }
                if (cookie.indexOf(name) === 0) {
                    return cookie.substring(name.length, cookie.length);
                }
            }
            return null;
        } else {
            // No CSRF token in localStorage mode
            return null;
        }
    };

    /**
     * Utility function to get stored user info (fallback for localStorage mode)
     */
    window.getCurrentUser = function() {
        if (!USE_SECURE_COOKIES) {
            try {
                const userStr = localStorage.getItem('sb_user');
                return userStr ? JSON.parse(userStr) : null;
            } catch (error) {
                console.error('Error parsing stored user data:', error);
                return null;
            }
        }
        return null; // User data comes from server in cookie mode
    };

    /**
     * Utility function to get stored token (fallback for localStorage mode)
     */
    window.getAuthToken = function() {
        if (!USE_SECURE_COOKIES) {
            return localStorage.getItem('sb_token');
        }
        return null; // Token is in httpOnly cookie
    };

    /**
     * Utility function to clear auth data
     */
    window.clearAuthData = function() {
        if (USE_SECURE_COOKIES) {
            // CSRF and auth cookies will be cleared by server
            delete window.csrfToken;
        } else {
            localStorage.removeItem('sb_token');
            localStorage.removeItem('sb_user');
        }
    };

})(); 