/**
 * Authentication Helper for Sports Betting Dashboard
 * Manages JWT tokens, auth state, and API calls with authentication
 * Supports both localStorage (dev) and httpOnly cookies (production)
 */

(function() {
    'use strict';

    // Configuration - should match login.js
    const USE_SECURE_COOKIES = true;

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
        if (USE_SECURE_COOKIES) {
            // Check for session cookie presence (not accessible via JS)
            // We'll make a quick API call to verify
            return checkCookieAuthentication();
        } else {
            const token = localStorage.getItem('sb_token');
            return token && token.length > 0;
        }
    }

    /**
     * Check authentication via cookie-based API call
     */
    async function checkCookieAuthentication() {
        try {
            const response = await fetch('/api/session/user', {
                credentials: 'include'
            });
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    /**
     * Get current user info
     */
    async function getCurrentUser() {
        if (USE_SECURE_COOKIES) {
            try {
                const response = await fetch('/api/session/user', {
                    credentials: 'include'
                });
                if (response.ok) {
                    return await response.json();
                }
                return null;
            } catch (error) {
                console.error('Error fetching user data:', error);
                return null;
            }
        } else {
            // localStorage fallback
            try {
                const userStr = localStorage.getItem('sb_user');
                return userStr ? JSON.parse(userStr) : null;
            } catch (error) {
                console.error('Error parsing user data:', error);
                return null;
            }
        }
    }

    /**
     * Get authentication token (for localStorage mode)
     */
    function getAuthToken() {
        if (!USE_SECURE_COOKIES) {
            return localStorage.getItem('sb_token');
        }
        return null; // Token is in httpOnly cookie
    }

    /**
     * Get CSRF token for API calls
     */
    function getCSRFToken() {
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
        }
        return null; // No CSRF in localStorage mode
    }

    /**
     * Update authentication UI based on current state
     */
    async function updateAuthUI() {
        const authStatus = document.getElementById('auth-status');
        if (!authStatus) return;

        if (await isAuthenticated()) {
            const user = await getCurrentUser();
            const userEmail = user ? user.email : 'Unknown User';
            const userRole = user ? user.role : 'free';
            
            authStatus.innerHTML = `
                <div class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                        <i class="fas fa-user me-1"></i>${userEmail}
                        <span class="badge bg-${getRoleBadgeColor(userRole)} ms-1">${userRole.toUpperCase()}</span>
                    </a>
                    <ul class="dropdown-menu">
                        <li><a class="dropdown-item" href="/profile"><i class="fas fa-user me-2"></i>Profile</a></li>
                        <li><a class="dropdown-item" href="/settings"><i class="fas fa-cog me-2"></i>Settings</a></li>
                        ${userRole === 'free' ? '<li><hr class="dropdown-divider"></li><li><a class="dropdown-item text-warning" href="/pricing"><i class="fas fa-star me-2"></i>Upgrade to Premium</a></li>' : ''}
                        <li><hr class="dropdown-divider"></li>
                        <li><a class="dropdown-item" href="#" id="logout-btn"><i class="fas fa-sign-out-alt me-2"></i>Logout</a></li>
                    </ul>
                </div>
            `;
            
            // Handle role-based UI elements
            handleRoleBasedUI(userRole);
        } else {
            authStatus.innerHTML = `
                <a class="nav-link" href="/login">
                    <i class="fas fa-sign-in-alt me-1"></i> Login
                </a>
            `;
        }
    }

    /**
     * Get badge color based on user role
     */
    function getRoleBadgeColor(role) {
        switch (role) {
            case 'admin': return 'danger';
            case 'subscriber': return 'success';
            case 'free': return 'secondary';
            default: return 'secondary';
        }
    }

    /**
     * Handle role-based UI elements and upgrade banner
     */
    function handleRoleBasedUI(userRole) {
        // Show/hide role-specific elements
        toggleElementsByRole('free-only', userRole === 'free');
        toggleElementsByRole('subscriber-only', userRole === 'subscriber' || userRole === 'admin');
        toggleElementsByRole('admin-only', userRole === 'admin');
        
        // Handle upgrade banner persistence
        handleUpgradeBanner();
    }

    /**
     * Toggle visibility of elements by role
     */
    function toggleElementsByRole(className, show) {
        const elements = document.querySelectorAll(`.${className}`);
        elements.forEach(element => {
            element.style.display = show ? 'block' : 'none';
        });
    }

    /**
     * Handle upgrade banner display and persistence
     */
    function handleUpgradeBanner() {
        const banner = document.getElementById('upgrade-banner');
        if (!banner) return;

        // Check if user has dismissed banner this session
        const userId = getCurrentUserId();
        const sessionKey = `upgrade_banner_dismissed_${userId || 'anonymous'}`;
        const isDismissed = sessionStorage.getItem(sessionKey) === 'true';

        if (isDismissed) {
            banner.style.display = 'none';
        }

        // Listen for banner close
        const closeBtn = banner.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                sessionStorage.setItem(sessionKey, 'true');
            });
        }
    }

    /**
     * Get current user ID for session management
     */
    function getCurrentUserId() {
        if (USE_SECURE_COOKIES) {
            // We'll need to extract from a cookie or make an API call
            return 'session_user'; // Placeholder for cookie-based sessions
        } else {
            try {
                const user = JSON.parse(localStorage.getItem('sb_user') || '{}');
                return user.id;
            } catch (error) {
                return null;
            }
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

        // Listen for storage changes (logout from other tabs) - localStorage mode only
        if (!USE_SECURE_COOKIES) {
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
            if (USE_SECURE_COOKIES) {
                // Use secure logout endpoint
                await fetch('/api/logout-secure', {
                    method: 'POST',
                    credentials: 'include'
                });
            } else {
                // Sign out from Supabase
                if (window.supabase) {
                    await window.supabase.auth.signOut();
                }
                
                // Clear local storage
                localStorage.removeItem('sb_token');
                localStorage.removeItem('sb_user');
            }
            
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
     * Make authenticated API request with CSRF protection and role handling
     */
    async function authenticatedFetch(url, options = {}) {
        if (USE_SECURE_COOKIES) {
            // Cookie-based authentication with CSRF
            const headers = {
                'Content-Type': 'application/json',
                ...options.headers
            };

            // Add CSRF token for state-changing operations
            const method = options.method || 'GET';
            if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
                const csrfToken = getCSRFToken();
                if (csrfToken) {
                    headers['X-CSRF-Token'] = csrfToken;
                }
            }

            const response = await fetch(url, {
                ...options,
                headers,
                credentials: 'include' // Include cookies
            });

            // Handle authentication errors
            if (response.status === 401) {
                updateAuthUI();
                redirectToLogin();
                throw new Error('Authentication expired. Please login again.');
            }

            // Handle CSRF errors
            if (response.status === 403) {
                const errorData = await response.json();
                if (errorData.detail && errorData.detail.includes('CSRF')) {
                    throw new Error('Security token expired. Please refresh the page.');
                }
            }

            // Handle successful responses with role data
            if (response.ok) {
                const data = await response.json();
                
                // Handle truncated responses for free users
                if (data.truncated && data.role === 'free') {
                    showUpgradeBannerWithData(data);
                }
                
                return data;
            }

            return response;
        } else {
            // localStorage-based authentication (development)
            const token = getAuthToken();
            
            if (!token) {
                throw new Error('No authentication token available');
            }

            const headers = {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                ...options.headers
            };

            const response = await fetch(url, {
                ...options,
                headers
            });

            // Handle authentication errors
            if (response.status === 401) {
                localStorage.removeItem('sb_token');
                localStorage.removeItem('sb_user');
                updateAuthUI();
                redirectToLogin();
                throw new Error('Authentication expired. Please login again.');
            }

            // Handle successful responses with role data
            if (response.ok) {
                const data = await response.json();
                
                // Handle truncated responses for free users
                if (data.truncated && data.role === 'free') {
                    showUpgradeBannerWithData(data);
                }
                
                return data;
            }

            return response;
        }
    }

    /**
     * Show upgrade banner with current data
     */
    function showUpgradeBannerWithData(data) {
        const banner = document.getElementById('upgrade-banner');
        if (banner && data.total_available && data.shown) {
            // Update banner with current data
            const shownElements = banner.querySelectorAll('[data-shown]');
            const totalElements = banner.querySelectorAll('[data-total]');
            
            shownElements.forEach(el => el.textContent = data.shown);
            totalElements.forEach(el => el.textContent = data.total_available);
            
            // Show banner if hidden and not dismissed
            const userId = getCurrentUserId();
            const sessionKey = `upgrade_banner_dismissed_${userId || 'anonymous'}`;
            const isDismissed = sessionStorage.getItem(sessionKey) === 'true';
            
            if (!isDismissed) {
                banner.classList.add('show');
                banner.style.display = 'block';
            }
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
     * Refresh authentication token (Supabase handles this automatically)
     */
    async function refreshAuthToken() {
        if (!USE_SECURE_COOKIES && window.supabase) {
            try {
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
            } catch (error) {
                console.error('Error refreshing token:', error);
            }
        }
        
        return null;
    }

    // Export global functions for use by other scripts
    window.authHelpers = {
        isAuthenticated,
        getCurrentUser,
        getAuthToken,
        getCSRFToken,
        authenticatedFetch,
        logout,
        refreshAuthToken,
        updateAuthUI,
        showAuthMessage
    };

})(); 