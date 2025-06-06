/**
 * Authentication Helper for Sports Betting Dashboard
 * Manages JWT tokens, auth state, and API calls with authentication
 * Supports both localStorage (dev) and httpOnly cookies (production)
 */

(function() {
    'use strict';
    console.log('auth.js: IIFE started'); // DEBUG

    // Configuration - should match login.js
    const USE_SECURE_COOKIES = true;

    // Initialize auth when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        initializeAuth();
    });

    /**
     * Initialize authentication system
     */
    async function initializeAuth() {
        console.log('auth.js: Initializing authentication system');
        
        await updateAuthUI();
        setupAuthEventListeners();
        
        // Check if we're on a protected page without auth
        if (isProtectedPage() && !(await isAuthenticated())) {
            redirectToLogin();
        }
    }

    /**
     * Check if user is authenticated
     */
    async function isAuthenticated() {
        if (USE_SECURE_COOKIES) {
            // Check for session cookie presence via API call
            return await checkCookieAuthentication();
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
            console.error('Cookie auth check failed:', error);
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
                    const user = await response.json();
                    console.log('Got current user:', user);
                    return user;
                }
                console.log('User fetch failed:', response.status);
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
        if (!authStatus) {
            console.log('No auth-status element found');
            return;
        }

        console.log('Updating auth UI...');
        
        if (await isAuthenticated()) {
            const user = await getCurrentUser();
            const userRole = user ? user.role : 'free';
            
            console.log('User authenticated, Role:', userRole);
            
            authStatus.innerHTML = `
                <a class="nav-link" href="#" id="logout-btn">
                    <i class="fas fa-sign-out-alt me-1"></i> Logout
                </a>
            `;
            
            // Handle role-based UI elements
            handleRoleBasedUI(userRole);
            
            // Update server-side role display if needed
            updateServerRoleDisplay(user);
        } else {
            console.log('User not authenticated, showing login button');
            authStatus.innerHTML = `
                <a class="nav-link" href="/login">
                    <i class="fas fa-sign-in-alt me-1"></i> Login
                </a>
            `;
            
            // Clear any role-based UI
            handleRoleBasedUI('guest');
        }
    }

    /**
     * Update server-side role display elements
     */
    function updateServerRoleDisplay(user) {
        // Update role badges that might be rendered server-side
        const roleBadges = document.querySelectorAll('.user-role-badge');
        roleBadges.forEach(badge => {
            badge.textContent = user.role.toUpperCase();
            badge.className = `badge user-role-badge bg-${getRoleBadgeColor(user.role)} rounded-pill`;
        });
        
        // Update user email displays
        const emailDisplays = document.querySelectorAll('.user-email-display');
        emailDisplays.forEach(display => {
            display.textContent = user.email;
        });
        
        // Update upgrade visibility
        updateUpgradeVisibility(user);
        
        // Force page refresh if role significantly changed (e.g., free -> subscriber)
        const currentPageRole = document.body.dataset.userRole;
        if (currentPageRole && currentPageRole !== user.role) {
            console.log(`Role changed from ${currentPageRole} to ${user.role}, refreshing page`);
            // Set a flag to prevent infinite refresh loops
            if (!sessionStorage.getItem('role_refresh_done')) {
                sessionStorage.setItem('role_refresh_done', 'true');
                setTimeout(() => {
                    sessionStorage.removeItem('role_refresh_done');
                    location.reload();
                }, 100);
            }
        }
    }

    /**
     * Update upgrade visibility based on user
     */
    function updateUpgradeVisibility(user) {
        const upgradeCTA = document.getElementById('upgrade-cta');
        const upgradeBanner = document.getElementById('upgrade-banner');
        const manageBillingNav = document.getElementById('manage-billing-nav');
        
        if (user && user.role === 'free') {
            // Show upgrade CTA for free users
            if (upgradeCTA) upgradeCTA.classList.remove('d-none');
            // Hide manage billing for free users
            if (manageBillingNav) manageBillingNav.classList.add('d-none');
        } else if (user && (user.role === 'subscriber' || user.role === 'admin')) {
            // Hide upgrade CTA for premium users
            if (upgradeCTA) upgradeCTA.classList.add('d-none');
            // Show manage billing for subscribers
            if (manageBillingNav && user.role === 'subscriber') {
                manageBillingNav.classList.remove('d-none');
            }
            // Hide upgrade banner for premium users
            if (upgradeBanner) upgradeBanner.style.display = 'none';
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
        console.log('Handling role-based UI for role:', userRole);
        
        // Show/hide role-specific elements
        toggleElementsByRole('free-only', userRole === 'free');
        toggleElementsByRole('subscriber-only', userRole === 'subscriber' || userRole === 'admin');
        toggleElementsByRole('admin-only', userRole === 'admin');
        
        // Handle premium content visibility
        toggleElementsByRole('premium-content', userRole === 'subscriber' || userRole === 'admin');
        toggleElementsByRole('premium-feature', userRole === 'subscriber' || userRole === 'admin');
        
        // Handle upgrade banner persistence
        handleUpgradeBanner(userRole);
    }

    /**
     * Toggle visibility of elements by role
     */
    function toggleElementsByRole(className, show) {
        const elements = document.querySelectorAll(`.${className}`);
        console.log(`Found ${elements.length} elements with class ${className}, showing: ${show}`);
        elements.forEach(element => {
            if (show) {
                element.style.display = '';
                element.classList.remove('d-none');
            } else {
                element.style.display = 'none';
                element.classList.add('d-none');
            }
        });
    }

    /**
     * Handle upgrade banner display and persistence
     */
    function handleUpgradeBanner(userRole) {
        const banner = document.getElementById('upgrade-banner');
        if (!banner) return;

        // Hide banner for premium users
        if (userRole === 'subscriber' || userRole === 'admin') {
            banner.style.display = 'none';
            return;
        }

        // Check if user has dismissed banner this session
        const userId = getCurrentUserId();
        const sessionKey = `upgrade_banner_dismissed_${userId || 'anonymous'}`;
        const isDismissed = sessionStorage.getItem(sessionKey) === 'true';

        if (isDismissed) {
            banner.style.display = 'none';
        } else {
            banner.style.display = '';
        }

        // Listen for banner close
        const closeBtn = banner.querySelector('.btn-close');
        if (closeBtn && !closeBtn.hasAttribute('data-listener-added')) {
            closeBtn.setAttribute('data-listener-added', 'true');
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
        showAuthMessage,
        // Add method to force auth state refresh
        forceAuthRefresh: async function() {
            console.log('Forcing auth state refresh...');
            await updateAuthUI();
            
            // If we're authenticated, also refresh the page to get server-side content
            if (await isAuthenticated()) {
                const user = await getCurrentUser();
                if (user && user.role !== 'free') {
                    console.log('Premium user detected, refreshing to show full content');
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                }
            }
        }
    };

    // Listen for storage events (for cross-tab auth sync)
    window.addEventListener('storage', function(e) {
        if (e.key === 'auth_state_changed') {
            console.log('Auth state changed in another tab, refreshing...');
            window.authHelpers.forceAuthRefresh();
        }
    });

    // Add method to manually trigger auth refresh (useful for login success)
    window.triggerAuthRefresh = function() {
        localStorage.setItem('auth_state_changed', Date.now());
        localStorage.removeItem('auth_state_changed');
        window.authHelpers.forceAuthRefresh();
    };

    /**
     * DEBUG: Trigger manual data refresh for development
     */
    async function triggerManualRefreshDev() {
        console.log('auth.js: triggerManualRefreshDev() called'); // DEBUG
        const btn = document.getElementById('manual-refresh-dev-btn');
        if (!btn) return;

        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Refreshing...';

        try {
            // No CSRF needed if the debug endpoint doesn't require it,
            // or handle CSRF if your debug endpoint is protected similarly to other POSTs.
            const response = await fetch('/debug/trigger-refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                    // Add CSRF header here if your debug endpoint implements CSRF protection
                    // 'X-CSRF-Token': getCSRFToken() 
                },
                // credentials: 'include', // Only if sending cookies to a CSRF protected endpoint
            });

            const result = await response.json();

            if (response.ok && result.status === 'scheduled') {
                showAuthMessage(`Manual refresh task (ID: ${result.task_id}) scheduled. Check worker logs.`, 'success');
            } else {
                throw new Error(result.detail || 'Failed to start refresh task.');
            }
        } catch (error) {
            console.error('Manual refresh error:', error);
            showAuthMessage(`Error: ${error.message}`, 'error');
        } finally {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
    console.log('auth.js: About to expose triggerManualRefreshDev to window'); // DEBUG
    window.triggerManualRefreshDev = triggerManualRefreshDev; // Expose for the button
    console.log('auth.js: triggerManualRefreshDev EXPOSED to window', window.triggerManualRefreshDev); // DEBUG

})(); 