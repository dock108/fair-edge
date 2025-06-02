/**
 * Admin Dashboard JavaScript
 * Handles user management and system statistics
 */

// Global state
let currentPage = 1;
let currentFilters = {};
let systemStats = null;

// Initialize admin dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminDashboard();
});

/**
 * Initialize the admin dashboard
 */
async function initializeAdminDashboard() {
    try {
        // Load current admin user info
        await loadAdminUserInfo();
        
        // Load initial users data
        await loadUsers(1);
        
        // Set up event listeners
        setupEventListeners();
        
        // Load system stats if stats tab is active
        const statsTab = document.getElementById('stats-tab');
        if (statsTab && statsTab.classList.contains('active')) {
            await loadSystemStats();
        }
    } catch (error) {
        console.error('Error initializing admin dashboard:', error);
        showAlert('Failed to initialize admin dashboard', 'error');
    }
}

/**
 * Load current admin user information
 */
async function loadAdminUserInfo() {
    try {
        const response = await authenticatedFetch('/api/session/user', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const user = await response.json();
            document.getElementById('admin-user-email').textContent = user.email;
        } else {
            document.getElementById('admin-user-email').textContent = 'Unknown Admin';
        }
    } catch (error) {
        console.error('Error loading admin user info:', error);
        document.getElementById('admin-user-email').textContent = 'Error Loading';
    }
}

/**
 * Set up event listeners for the dashboard
 */
function setupEventListeners() {
    // Tab change listeners
    document.getElementById('stats-tab').addEventListener('click', async function() {
        if (!systemStats) {
            await loadSystemStats();
        }
    });
    
    // Search input with debouncing
    const searchInput = document.getElementById('user-search');
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchUsers();
        }, 500);
    });
    
    // Role filter change
    document.getElementById('role-filter').addEventListener('change', function() {
        searchUsers();
    });
    
    // Enter key support for search
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchUsers();
        }
    });
}

/**
 * Load users with pagination and filtering
 */
async function loadUsers(page = 1, search = '', role = '') {
    try {
        currentPage = page;
        currentFilters = { search, role };
        
        // Show loading state
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <div class="loading-spinner">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p class="mt-2 mb-0">Loading users...</p>
                    </div>
                </td>
            </tr>
        `;
        
        // Build query parameters
        const params = new URLSearchParams({
            page: page.toString(),
            limit: '50'
        });
        
        if (search) params.append('search', search);
        if (role) params.append('role', role);
        
        const response = await authenticatedFetch(`/api/admin/users?${params}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load users: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Populate users table
        populateUsersTable(data.users);
        
        // Update pagination
        updatePagination(data.pagination);
        
    } catch (error) {
        console.error('Error loading users:', error);
        showAlert('Failed to load users', 'error');
        
        // Show error state
        const tbody = document.getElementById('users-table-body');
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <div class="error-message">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Failed to load users. Please try again.
                    </div>
                </td>
            </tr>
        `;
    }
}

/**
 * Populate the users table with data
 */
function populateUsersTable(users) {
    const tbody = document.getElementById('users-table-body');
    
    if (users.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center py-4">
                    <div class="text-muted">
                        <i class="fas fa-inbox me-2"></i>
                        No users found matching your criteria.
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = users.map(user => {
        const createdDate = user.created_at ? new Date(user.created_at).toLocaleDateString() : 'Unknown';
        const lastLogin = user.last_sign_in_at ? new Date(user.last_sign_in_at).toLocaleDateString() : 'Never';
        
        const roleClass = `role-${user.role}`;
        const subscriptionClass = user.subscription_status === 'active' ? 'subscription-active' : 'subscription-inactive';
        
        return `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-user me-2 text-muted"></i>
                        ${user.email}
                    </div>
                </td>
                <td>
                    <span class="role-badge ${roleClass}">
                        ${user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                    </span>
                </td>
                <td>
                    <span class="${subscriptionClass}">
                        ${user.subscription_status || 'none'}
                    </span>
                </td>
                <td>
                    <small class="text-muted">
                        <i class="fas fa-calendar-alt me-1"></i>
                        ${createdDate}
                    </small>
                </td>
                <td>
                    <small class="text-muted">
                        <i class="fas fa-clock me-1"></i>
                        ${lastLogin}
                    </small>
                </td>
                <td>
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-primary" 
                                onclick="showChangeRoleModal('${user.id}', '${user.email}', '${user.role}')"
                                title="Change Role">
                            <i class="fas fa-user-cog"></i>
                        </button>
                        ${user.role !== 'admin' ? `
                            <button type="button" class="btn btn-outline-danger"
                                    onclick="confirmDeleteUser('${user.id}', '${user.email}')"
                                    title="Delete User">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Update pagination controls
 */
function updatePagination(pagination) {
    const container = document.getElementById('users-pagination');
    
    if (pagination.total_pages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let paginationHTML = '';
    
    // Previous button
    if (pagination.has_prev) {
        paginationHTML += `
            <li class="page-item">
                <button class="page-link" onclick="loadUsers(${pagination.page - 1}, '${currentFilters.search || ''}', '${currentFilters.role || ''}')">
                    <i class="fas fa-chevron-left"></i>
                </button>
            </li>
        `;
    }
    
    // Page numbers
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.total_pages, pagination.page + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === pagination.page ? 'active' : '';
        paginationHTML += `
            <li class="page-item ${activeClass}">
                <button class="page-link" onclick="loadUsers(${i}, '${currentFilters.search || ''}', '${currentFilters.role || ''}')">${i}</button>
            </li>
        `;
    }
    
    // Next button
    if (pagination.has_next) {
        paginationHTML += `
            <li class="page-item">
                <button class="page-link" onclick="loadUsers(${pagination.page + 1}, '${currentFilters.search || ''}', '${currentFilters.role || ''}')">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </li>
        `;
    }
    
    container.innerHTML = paginationHTML;
}

/**
 * Search users based on current filters
 */
function searchUsers() {
    const search = document.getElementById('user-search').value.trim();
    const role = document.getElementById('role-filter').value;
    
    loadUsers(1, search, role);
}

/**
 * Clear all filters and reload users
 */
function clearFilters() {
    document.getElementById('user-search').value = '';
    document.getElementById('role-filter').value = '';
    loadUsers(1);
}

/**
 * Show the change role modal
 */
function showChangeRoleModal(userId, userEmail, currentRole) {
    document.getElementById('change-user-id').value = userId;
    document.getElementById('change-user-email').value = userEmail;
    document.getElementById('new-role').value = currentRole;
    document.getElementById('change-reason').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('roleChangeModal'));
    modal.show();
}

/**
 * Confirm role change
 */
async function confirmRoleChange() {
    try {
        const userId = document.getElementById('change-user-id').value;
        const newRole = document.getElementById('new-role').value;
        const reason = document.getElementById('change-reason').value;
        const userEmail = document.getElementById('change-user-email').value;
        
        if (!newRole) {
            showAlert('Please select a role', 'error');
            return;
        }
        
        // Show loading state
        const submitBtn = document.querySelector('#roleChangeModal .btn-danger');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Updating...';
        
        const response = await authenticatedFetch(`/api/admin/users/${userId}/role`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                role: newRole,
                reason: reason || null
            }),
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update role');
        }
        
        const result = await response.json();
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('roleChangeModal'));
        modal.hide();
        
        // Show success message
        showAlert(`Successfully updated ${userEmail} role to ${newRole}`, 'success');
        
        // Reload users
        await loadUsers(currentPage, currentFilters.search, currentFilters.role);
        
    } catch (error) {
        console.error('Error updating user role:', error);
        showAlert(`Failed to update role: ${error.message}`, 'error');
    } finally {
        // Reset button state
        const submitBtn = document.querySelector('#roleChangeModal .btn-danger');
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

/**
 * Confirm user deletion
 */
function confirmDeleteUser(userId, userEmail) {
    if (confirm(`Are you sure you want to DELETE user "${userEmail}"?\n\nThis action is irreversible and will:\n- Delete their account permanently\n- Cancel any active subscriptions\n- Remove all user data\n\nType "DELETE" to confirm:`)) {
        const confirmation = prompt('Type "DELETE" to confirm this action:');
        if (confirmation === 'DELETE') {
            deleteUser(userId, userEmail);
        }
    }
}

/**
 * Delete a user account
 */
async function deleteUser(userId, userEmail) {
    try {
        const response = await authenticatedFetch(`/api/admin/users/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete user');
        }
        
        showAlert(`Successfully deleted user ${userEmail}`, 'success');
        
        // Reload users
        await loadUsers(currentPage, currentFilters.search, currentFilters.role);
        
    } catch (error) {
        console.error('Error deleting user:', error);
        showAlert(`Failed to delete user: ${error.message}`, 'error');
    }
}

/**
 * Load system statistics
 */
async function loadSystemStats() {
    try {
        const response = await authenticatedFetch('/api/admin/stats', {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load stats: ${response.status}`);
        }
        
        systemStats = await response.json();
        
        // Update overview cards
        updateOverviewCards(systemStats);
        
        // Update detailed metrics
        updateDetailedMetrics(systemStats);
        
        // Update timestamp
        document.getElementById('stats-timestamp').textContent = new Date().toLocaleTimeString();
        
    } catch (error) {
        console.error('Error loading system stats:', error);
        showAlert('Failed to load system statistics', 'error');
        
        // Show error state in metrics
        showMetricsError();
    }
}

/**
 * Update overview cards with system stats
 */
function updateOverviewCards(stats) {
    // Total users
    const totalUsers = stats.database_stats?.total_users || 0;
    document.getElementById('total-users').textContent = totalUsers.toLocaleString();
    
    // Active subscribers
    const activeSubscribers = stats.database_stats?.active_subscriptions || 0;
    document.getElementById('active-subscribers').textContent = activeSubscribers.toLocaleString();
    
    // Cached opportunities
    const cachedOpportunities = stats.cache_stats?.opportunities_cached || 0;
    document.getElementById('cached-opportunities').textContent = cachedOpportunities.toLocaleString();
    
    // System uptime (simplified)
    const uptimeDays = stats.cache_stats?.redis_uptime_days || 0;
    document.getElementById('system-uptime').textContent = `${uptimeDays}d`;
}

/**
 * Update detailed metrics sections
 */
function updateDetailedMetrics(stats) {
    // Cache metrics
    updateCacheMetrics(stats.cache_stats);
    
    // Performance metrics
    updatePerformanceMetrics(stats.performance_stats);
    
    // User metrics
    updateUserMetrics(stats.database_stats);
    
    // Application metrics
    updateAppMetrics(stats.application_stats);
}

/**
 * Update cache metrics section
 */
function updateCacheMetrics(cacheStats) {
    const container = document.getElementById('cache-metrics');
    
    if (cacheStats?.error) {
        container.innerHTML = `<div class="text-danger">Error: ${cacheStats.error}</div>`;
        return;
    }
    
    container.innerHTML = `
        <div class="metric-row">
            <span class="metric-label">Opportunities Cached</span>
            <span class="metric-value">${(cacheStats?.opportunities_cached || 0).toLocaleString()}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Memory Used</span>
            <span class="metric-value">${cacheStats?.redis_memory_used || 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Memory Peak</span>
            <span class="metric-value">${cacheStats?.redis_memory_peak || 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Connected Clients</span>
            <span class="metric-value">${cacheStats?.redis_connected_clients || 0}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Last Update</span>
            <span class="metric-value">${cacheStats?.last_update ? new Date(cacheStats.last_update).toLocaleString() : 'Never'}</span>
        </div>
    `;
}

/**
 * Update performance metrics section
 */
function updatePerformanceMetrics(perfStats) {
    const container = document.getElementById('performance-metrics');
    
    if (perfStats?.error) {
        container.innerHTML = `<div class="text-danger">Error: ${perfStats.error}</div>`;
        return;
    }
    
    container.innerHTML = `
        <div class="metric-row">
            <span class="metric-label">CPU Usage</span>
            <span class="metric-value">${perfStats?.cpu_usage_percent !== undefined ? `${perfStats.cpu_usage_percent.toFixed(1)}%` : 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Memory Usage</span>
            <span class="metric-value">${perfStats?.memory_usage_percent !== undefined ? `${perfStats.memory_usage_percent.toFixed(1)}%` : 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Memory Available</span>
            <span class="metric-value">${perfStats?.memory_available_mb ? `${perfStats.memory_available_mb} MB` : 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Disk Usage</span>
            <span class="metric-value">${perfStats?.disk_usage_percent !== undefined ? `${perfStats.disk_usage_percent.toFixed(1)}%` : 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Disk Free</span>
            <span class="metric-value">${perfStats?.disk_free_gb ? `${perfStats.disk_free_gb} GB` : 'Unknown'}</span>
        </div>
    `;
}

/**
 * Update user metrics section
 */
function updateUserMetrics(dbStats) {
    const container = document.getElementById('user-metrics');
    
    if (dbStats?.error) {
        container.innerHTML = `<div class="text-danger">Error: ${dbStats.error}</div>`;
        return;
    }
    
    const usersByRole = dbStats?.users_by_role || {};
    const newUsers = dbStats?.new_users || {};
    
    container.innerHTML = `
        <div class="metric-row">
            <span class="metric-label">Total Users</span>
            <span class="metric-value">${(dbStats?.total_users || 0).toLocaleString()}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Admin Users</span>
            <span class="metric-value">${usersByRole.admin || 0}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Subscribers</span>
            <span class="metric-value">${usersByRole.subscriber || 0}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Free Users</span>
            <span class="metric-value">${usersByRole.free || 0}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">New (7 days)</span>
            <span class="metric-value">${newUsers.last_7_days || 0}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">New (30 days)</span>
            <span class="metric-value">${newUsers.last_30_days || 0}</span>
        </div>
    `;
}

/**
 * Update application metrics section
 */
function updateAppMetrics(appStats) {
    const container = document.getElementById('app-metrics');
    
    if (appStats?.error) {
        container.innerHTML = `<div class="text-danger">Error: ${appStats.error}</div>`;
        return;
    }
    
    container.innerHTML = `
        <div class="metric-row">
            <span class="metric-label">Version</span>
            <span class="metric-value">${appStats?.version || 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Environment</span>
            <span class="metric-value">${appStats?.environment || 'Unknown'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Celery Status</span>
            <span class="metric-value">${appStats?.celery_stats?.error ? 'Error' : 'Available'}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Active WebSockets</span>
            <span class="metric-value">${appStats?.active_websockets || 0}</span>
        </div>
    `;
}

/**
 * Show error state in metrics
 */
function showMetricsError() {
    const sections = ['cache-metrics', 'performance-metrics', 'user-metrics', 'app-metrics'];
    sections.forEach(sectionId => {
        document.getElementById(sectionId).innerHTML = `
            <div class="text-danger text-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Failed to load metrics
            </div>
        `;
    });
}

/**
 * Refresh system statistics
 */
async function refreshStats() {
    const refreshBtn = document.querySelector('button[onclick="refreshStats()"]');
    const originalContent = refreshBtn.innerHTML;
    
    try {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin me-2"></i>Refreshing...';
        
        await loadSystemStats();
        
        showAlert('Statistics refreshed successfully', 'success');
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
        showAlert('Failed to refresh statistics', 'error');
    } finally {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = originalContent;
    }
}

/**
 * Show alert message
 */
function showAlert(message, type = 'info') {
    const alertContainer = document.getElementById('alert-container');
    const alertId = 'alert-' + Date.now();
    
    const alertClass = type === 'error' ? 'alert-danger' : type === 'success' ? 'alert-success' : 'alert-info';
    const iconClass = type === 'error' ? 'fa-exclamation-circle' : type === 'success' ? 'fa-check-circle' : 'fa-info-circle';
    
    const alertHTML = `
        <div class="alert ${alertClass} alert-dismissible fade show" role="alert" id="${alertId}">
            <i class="fas ${iconClass} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    
    alertContainer.insertAdjacentHTML('beforeend', alertHTML);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }
    }, 5000);
} 