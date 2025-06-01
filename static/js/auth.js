/**
 * Authentication Helper for Sports Betting Dashboard
 * Manages JWT tokens, auth state, and API calls with authentication
 */

(function() {
    'use strict';

    // Initialize auth when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeAuth();
    });

    /**
     * Initialize authentication system
     */
    function initializeAuth() {
        updateAuthUI();
        setupAuthEventListeners();
        
        // Check if we're on a protected page without auth
        if (isProtectedPage() && !isAuthenticated()) {
            redirectToLogin();
        }
    }

    /**
     * Check if user is authenticated
     */
    function isAuthenticated() {
        const token = localStorage.getItem('sb_token');
        return token && token.length > 0;
    }

    /**
     * Get current user info from localStorage
     */
    function getCurrentUser() {
        try {
            const userStr = localStorage.getItem('sb_user');
            return userStr ? JSON.parse(userStr) : null;
        } catch (error) {
            console.error('Error parsing user data:', error);
            return null;
        }
    }

    /**
     * Get authentication token
     */
    function getAuthToken() {
        return localStorage.getItem('sb_token');
    }

    /**
     * Update authentication UI based on current state
     */
    function updateAuthUI() {
        const authStatus = document.getElementById('auth-status');
        if (!authStatus) return;

        if (isAuthenticated()) {
            const user = getCurrentUser();
            const userEmail = user ? user.email : 'Unknown User';
            const userRole = user ? user.role : 'free';
            
            authStatus.innerHTML = `
                <div class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="fas fa-user me-1"></i>${userEmail}
                        <span class="badge bg-secondary ms-1">${userRole}</span>
                    </a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="/profile"><i class="fas fa-user me-2"></i>Profile</a></li>
                        <li><a class="dropdown-item" href="/settings"><i class="fas fa-cog me-2"></i>Settings</a></li>
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="#" id="logout-btn"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
                    </ul>
                </div>
            `;
        } else {
            authStatus.innerHTML = `
                <a class="nav-link" href="/login">
                    <i class="fas fa-sign-in-alt me-1"></i> Login
                </a>
            `;
        }
    }

    /**
     * Setup event listeners for auth-related actions
     */
    function setupAuthEventListeners() {
        // Logout button listener (delegated to handle dynamic content)
        document.addEventListener('click', function(e) {
            if (e.target && e.target.id === 'logout-btn') {
                e.preventDefault();
                logout();
            }
        });

        // Listen for storage changes (logout from other tabs)
        window.addEventListener('storage', function(e) {
            if (e.key === 'sb_token' && !e.newValue) {
                // Token was removed in another tab
                updateAuthUI();
                if (isProtectedPage()) {
                    redirectToLogin();
                }
            }
        });
    }

    /**
     * Check if current page requires authentication
     */
    function isProtectedPage() {
        const protectedPaths = ['/dashboard', '/premium', '/profile', '/settings'];
        const currentPath = window.location.pathname;
        return protectedPaths.some(path => currentPath.startsWith(path));
    }

    /**
     * Redirect to login page
     */
    function redirectToLogin() {
        window.location.href = '/login';
    }

    /**
     * Logout user
     */
    async function logout() {
        try {
            // Sign out from Supabase
            if (window.supabase) {
                await window.supabase.auth.signOut();
            }
            
            // Clear local storage
            localStorage.removeItem('sb_token');
            localStorage.removeItem('sb_user');
            
            // Update UI
            updateAuthUI();
            
            // Show success message
            showAuthMessage('Logged out successfully', 'success');
            
            // Redirect to login after short delay
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
            
        } catch (error) {
            console.error('Logout error:', error);
            showAuthMessage('Error during logout', 'error');
        }
    }

    /**
     * Make authenticated API request
     */
    async function authenticatedFetch(url, options = {}) {
        const token = getAuthToken();
        
        if (!token) {
            throw new Error('No authentication token available');
        }

        // Set up headers
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
            ...options.headers
        };

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            // Handle authentication errors
            if (response.status === 401) {
                // Token expired or invalid
                localStorage.removeItem('sb_token');
                localStorage.removeItem('sb_user');
                updateAuthUI();
                redirectToLogin();
                throw new Error('Authentication expired. Please login again.');
            }

            return response;
        } catch (error) {
            console.error('Authenticated fetch error:', error);
            throw error;
        }
    }

    /**
     * Show authentication-related messages
     */
    function showAuthMessage(message, type = 'info') {
        // Create or update message element
        let messageEl = document.getElementById('auth-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'auth-message';
            messageEl.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 15px 20px;
                border-radius: 8px;
                z-index: 9999;
                font-weight: 500;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: opacity 0.3s ease;
            `;
            document.body.appendChild(messageEl);
        }

        // Set message and styling based on type
        messageEl.textContent = message;
        messageEl.style.display = 'block';
        messageEl.style.opacity = '1';
        
        switch (type) {
            case 'success':
                messageEl.style.backgroundColor = '#d4edda';
                messageEl.style.color = '#155724';
                messageEl.style.border = '1px solid #c3e6cb';
                break;
            case 'error':
                messageEl.style.backgroundColor = '#f8d7da';
                messageEl.style.color = '#721c24';
                messageEl.style.border = '1px solid #f5c6cb';
                break;
            default:
                messageEl.style.backgroundColor = '#e2e3e5';
                messageEl.style.color = '#383d41';
                messageEl.style.border = '1px solid #d6d8db';
        }

        // Auto-hide after 3 seconds
        setTimeout(() => {
            messageEl.style.opacity = '0';
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 300);
        }, 3000);
    }

    /**
     * Refresh authentication token (if using auto-refresh)
     */
    async function refreshAuthToken() {
        try {
            if (window.supabase) {
                const { data: { session }, error } = await window.supabase.auth.getSession();
                
                if (session && !error) {
                    localStorage.setItem('sb_token', session.access_token);
                    
                    if (session.user) {
                        localStorage.setItem('sb_user', JSON.stringify({
                            id: session.user.id,
                            email: session.user.email,
                            role: session.user.user_metadata?.role || 'free'
                        }));
                    }
                    
                    updateAuthUI();
                    return session.access_token;
                }
            }
        } catch (error) {
            console.error('Error refreshing token:', error);
        }
        
        return null;
    }

    // Export global functions for use by other scripts
    window.authHelpers = {
        isAuthenticated,
        getCurrentUser,
        getAuthToken,
        authenticatedFetch,
        logout,
        refreshAuthToken,
        updateAuthUI,
        showAuthMessage
    };

})(); 