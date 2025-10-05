/**
 * Admin Page JavaScript
 * 
 * Handles all functionality for the admin management page
 */

class AdminPage {
    constructor() {
        this.users = [];
        this.stats = {};
        this.init();
    }

    async init() {
        this.checkAuth();
        await this.loadAdminData();
        // Delay event binding to ensure DOM is ready
        setTimeout(() => {
            this.bindEvents();
        }, 100);
    }

    async checkAuth() {
        // Try multiple token sources - match API Keys/Groups pattern exactly
        const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
        
        console.log('=== ADMIN AUTH DEBUG ===');
        console.log('token found:', !!token);
        console.log('localStorage keys:', Object.keys(localStorage));
        console.log('localStorage.token:', localStorage.getItem('token'));
        console.log('localStorage.auth_token:', localStorage.getItem('auth_token'));
        
        if (!token) {
            console.log('No token found, trying cookie auth...');
            // Try to check if we're authenticated via cookies by making an API call
            try {
                console.log('Making fetch to /api/auth/me...');
                const response = await fetch('/api/auth/me');
                console.log('Response status:', response.status, 'OK:', response.ok);
                
                if (response.ok) {
                    const user = await response.json();
                    console.log('Cookie auth user:', user);
                    
                    // Check admin status
                    if (!user.is_admin) {
                        console.log('User is not admin, redirecting in 5 seconds...');
                        setTimeout(() => {
                            window.location.href = '/';
                        }, 5000);
                        return;
                    }
                    
                    console.log('Cookie-based admin auth successful');
                    return; // SUCCESS - match API Keys pattern
                }
            } catch (error) {
                console.log('Cookie auth error:', error);
            }
            
            // No authentication found, redirect
            console.log('No valid authentication found, redirecting in 10 seconds...');
            console.log('You have 10 seconds to check the console and localStorage');
            setTimeout(() => {
                window.location.href = '/';
            }, 10000);
            return;
        }
        
        // We have a token, verify it works - match API Keys pattern exactly
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const user = await response.json();
                
                // Check admin status
                if (!user.is_admin) {
                    console.log('User is not admin, redirecting');
                    window.location.href = '/';
                    return;
                }
                
                console.log('Token-based admin auth successful for user:', user.username);
                return; // SUCCESS - match API Keys pattern
            }
        } catch (error) {
            console.log('Token verification error:', error);
        }
        
        // Token is invalid, redirect - match API Keys pattern exactly
        console.log('Token verification failed, redirecting');
        window.location.href = '/';
    }

    async loadAdminData() {
        try {
            // Check for authentication tokens (JWT or API key)
            const jwtToken = localStorage.getItem('token') || localStorage.getItem('auth_token');
            const apiKey = localStorage.getItem('api_key');
            
            // Determine which token to use
            const authToken = apiKey || jwtToken;
            
            if (!authToken) {
                console.log('No authentication token found');
                window.location.href = '/';
                return;
            }
            
            console.log('Using authentication:', apiKey ? 'API Key' : 'JWT Token');

            // Load stats
            const statsResponse = await fetch('/api/admin/stats', {
                headers: authToken ? {
                    'Authorization': `Bearer ${authToken}`
                } : {},
                credentials: 'include'
            });

            if (!statsResponse.ok) {
                throw new Error('Failed to load stats');
            }

            this.stats = await statsResponse.json();
            this.updateStatsDisplay();

            // Load users
            const usersResponse = await fetch('/api/admin/users', {
                headers: authToken ? {
                    'Authorization': `Bearer ${authToken}`
                } : {},
                credentials: 'include'
            });

            if (!usersResponse.ok) {
                throw new Error('Failed to load users');
            }

            this.users = await usersResponse.json();
            this.updateUsersDisplay();

        } catch (error) {
            console.error('Error loading admin data:', error);
            this.showError('Failed to load admin data: ' + error.message);
        }
    }

    updateStatsDisplay() {
        document.getElementById('total-users').textContent = this.stats.total_users || 0;
        document.getElementById('active-users').textContent = this.stats.active_users || 0;
        document.getElementById('total-boards').textContent = this.stats.total_boards || 0;
        document.getElementById('total-tasks').textContent = this.stats.total_tasks || 0;
    }

    updateUsersDisplay() {
        const usersList = document.getElementById('users-list');
        usersList.innerHTML = '';

        this.users.forEach(user => {
            const userRow = document.createElement('div');
            userRow.className = 'user-row';
            userRow.innerHTML = `
                <div>${user.username}</div>
                <div>${user.email}</div>
                <div>
                    <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                        ${user.is_active ? 'Active' : 'Inactive'}
                    </span>
                </div>
                <div>
                    <span class="admin-badge ${user.is_admin ? 'admin' : 'user'}">
                        ${user.is_admin ? 'Admin' : 'User'}
                    </span>
                </div>
                <div>${user.board_count || 0}</div>
                <div>${user.task_count || 0}</div>
                <div class="user-actions">
                    <button class="btn btn-sm ${user.is_active ? 'btn-warning' : 'btn-success'}" 
                            onclick="adminPage.toggleUserStatus(${user.id}, ${!user.is_active})">
                        ${user.is_active ? 'Disable' : 'Enable'}
                    </button>
                    <button class="btn btn-sm ${user.is_admin ? 'btn-secondary' : 'btn-primary'}" 
                            onclick="adminPage.toggleAdminStatus(${user.id}, ${!user.is_admin})">
                        ${user.is_admin ? 'Remove Admin' : 'Make Admin'}
                    </button>
                </div>
            `;
            usersList.appendChild(userRow);
        });

        document.getElementById('users-loading').style.display = 'none';
        document.getElementById('users-content').style.display = 'block';
    }

    async toggleUserStatus(userId, newStatus) {
        try {
            const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'PATCH',
                headers: {
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    is_active: newStatus
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update user status');
            }

            const updatedUser = await response.json();
            
            // Update local data
            const userIndex = this.users.findIndex(u => u.id === userId);
            if (userIndex !== -1) {
                this.users[userIndex] = updatedUser;
                this.updateUsersDisplay();
            }

            // Reload stats
            await this.loadStats();

        } catch (error) {
            console.error('Error updating user status:', error);
            this.showError('Failed to update user status: ' + error.message);
        }
    }

    async toggleAdminStatus(userId, newStatus) {
        try {
            const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
            const response = await fetch(`/api/admin/users/${userId}`, {
                method: 'PATCH',
                headers: {
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify({
                    is_admin: newStatus
                })
            });

            if (!response.ok) {
                throw new Error('Failed to update admin status');
            }

            const updatedUser = await response.json();
            
            // Update local data
            const userIndex = this.users.findIndex(u => u.id === userId);
            if (userIndex !== -1) {
                this.users[userIndex] = updatedUser;
                this.updateUsersDisplay();
            }

        } catch (error) {
            console.error('Error updating admin status:', error);
            this.showError('Failed to update admin status: ' + error.message);
        }
    }

    async loadStats() {
        try {
            const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
            const response = await fetch('/api/admin/stats', {
                headers: token ? {
                    'Authorization': `Bearer ${token}`
                } : {},
                credentials: 'include'
            });

            if (response.ok) {
                this.stats = await response.json();
                this.updateStatsDisplay();
            }
        } catch (error) {
            console.error('Error reloading stats:', error);
        }
    }

    showError(message) {
        const errorDiv = document.getElementById('error-message');
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    }

    bindEvents() {
        // Theme toggle
        this.initTheme();
        
        // User menu
        this.initUserMenu();
        
        // Set user name in header
        this.setUserName();
    }

    initTheme() {
        const themeToggle = document.getElementById('theme-toggle');
        if (!themeToggle) return;
        
        const themeIcon = themeToggle.querySelector('i');
        const currentTheme = document.documentElement.getAttribute('data-theme');
        
        // Update icon based on current theme
        if (themeIcon) {
            themeIcon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update icon
            if (themeIcon) {
                themeIcon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
            }
        });
    }

    initUserMenu() {
        const userMenuBtn = document.getElementById('user-menu-btn');
        const userDropdown = document.getElementById('user-dropdown');
        const userLogout = document.getElementById('user-logout');

        if (userMenuBtn && userDropdown) {
            userMenuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                userDropdown.style.display = userDropdown.style.display === 'none' ? 'block' : 'none';
            });

            // Close dropdown when clicking outside
            document.addEventListener('click', (e) => {
                if (!e.target.closest('.user-menu')) {
                    userDropdown.style.display = 'none';
                }
            });
        }

        if (userLogout) {
            userLogout.addEventListener('click', (e) => {
                e.preventDefault();
                localStorage.removeItem('token');
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user');
                window.location.href = '/';
            });
        }
    }

    setUserName() {
        // Set user name in header
        const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
        if (token) {
            fetch('/api/auth/me', {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            })
            .then(response => response.ok ? response.json() : null)
            .then(user => {
                if (user) {
                    const userNameEl = document.getElementById('user-name');
                    if (userNameEl) {
                        userNameEl.textContent = user.full_name || user.username || 'User';
                    }
                }
            })
            .catch(console.error);
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.adminPage = new AdminPage();
});
