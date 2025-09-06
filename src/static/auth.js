/**
 * Authentication module for Simple Kanban Board
 * Handles login, signup, and Google OIDC integration
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.token = localStorage.getItem('auth_token');
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthState();
    }

    bindEvents() {
        // Form switching
        document.getElementById('show-signup')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showSignupForm();
        });

        document.getElementById('show-login')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.showLoginForm();
        });

        // Email/Password forms
        document.getElementById('login-email-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleEmailLogin(e.target);
        });

        document.getElementById('signup-email-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleEmailSignup(e.target);
        });

        // Google OIDC buttons
        document.getElementById('google-login-btn')?.addEventListener('click', () => {
            this.handleGoogleAuth();
        });

        document.getElementById('google-signup-btn')?.addEventListener('click', () => {
            this.handleGoogleAuth();
        });

        // User menu
        document.getElementById('user-menu-btn')?.addEventListener('click', () => {
            this.toggleUserMenu();
        });

        document.getElementById('user-logout')?.addEventListener('click', (e) => {
            e.preventDefault();
            this.logout();
        });

        // Close user menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.user-menu')) {
                this.closeUserMenu();
            }
        });
    }

    async checkAuthState() {
        // First check for token in localStorage (email/password auth)
        if (this.token) {
            try {
                const response = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });

                if (response.ok) {
                    this.currentUser = await response.json();
                    this.showMainApp();
                    return;
                }
            } catch (error) {
                console.error('Auth check failed:', error);
            }
            
            // Token is invalid, remove it
            this.clearAuth();
        }
        
        // Check for cookie-based auth (OIDC)
        try {
            const response = await fetch('/api/auth/me', {
                credentials: 'include' // Include cookies
            });

            if (response.ok) {
                this.currentUser = await response.json();
                this.showMainApp();
                return;
            }
        } catch (error) {
            console.error('Cookie auth check failed:', error);
        }
        
        this.showAuthScreen();
    }

    showAuthScreen() {
        document.getElementById('auth-screen').style.display = 'flex';
        document.getElementById('main-app').style.display = 'none';
    }

    showMainApp() {
        document.getElementById('auth-screen').style.display = 'none';
        document.getElementById('main-app').style.display = 'block';
        
        if (this.currentUser) {
            document.getElementById('user-name').textContent = 
                this.currentUser.full_name || this.currentUser.username || 'User';
        }
        
        // Initialize the main kanban app
        if (window.initializeKanbanApp) {
            window.initializeKanbanApp();
        }
    }

    showLoginForm() {
        document.getElementById('login-form').style.display = 'block';
        document.getElementById('signup-form').style.display = 'none';
    }

    showSignupForm() {
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('signup-form').style.display = 'block';
    }

    async handleEmailLogin(form) {
        const formData = new FormData(form);
        const loginData = {
            username: formData.get('email'), // API expects username field
            password: formData.get('password')
        };

        try {
            this.setLoading(true);
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(loginData)
            });

            const data = await response.json();

            if (response.ok) {
                this.setAuth(data.access_token, data.user);
                this.showNotification('Login successful!', 'success');
                this.showMainApp();
            } else {
                this.showNotification(data.detail || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showNotification('Login failed. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async handleEmailSignup(form) {
        const formData = new FormData(form);
        const password = formData.get('password');
        const confirmPassword = formData.get('confirm_password');

        if (password !== confirmPassword) {
            this.showNotification('Passwords do not match', 'error');
            return;
        }

        const signupData = {
            username: formData.get('username'),
            email: formData.get('email'),
            full_name: formData.get('full_name'),
            password: password
        };

        try {
            this.setLoading(true);
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(signupData)
            });

            const data = await response.json();

            if (response.ok) {
                this.showNotification('Account created successfully! Please log in.', 'success');
                this.showLoginForm();
                // Pre-fill login email
                document.getElementById('login-email').value = signupData.email;
            } else {
                this.showNotification(data.detail || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Signup error:', error);
            this.showNotification('Registration failed. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async handleGoogleAuth() {
        try {
            this.setLoading(true);
            const response = await fetch('/api/oidc/auth/google', {
                method: 'POST'
            });

            const data = await response.json();

            if (response.ok) {
                // Store state for callback verification
                sessionStorage.setItem('oauth_state', data.state);
                // Redirect to Google OAuth
                window.location.href = data.auth_url;
            } else {
                this.showNotification(data.detail || 'Google authentication failed', 'error');
            }
        } catch (error) {
            console.error('Google auth error:', error);
            this.showNotification('Google authentication failed. Please try again.', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async handleOAuthCallback() {
        // OAuth callback is now handled server-side with redirect
        // Just clean up the URL and check auth state
        this.clearOAuthState();
        window.history.replaceState({}, document.title, window.location.pathname);
        
        // Check if we're now authenticated (cookie-based)
        await this.checkAuthState();
        
        if (this.currentUser) {
            this.showNotification('Login successful!', 'success');
        } else {
            this.showNotification('Authentication failed. Please try again.', 'error');
        }
    }

    setAuth(token, user) {
        this.token = token;
        this.currentUser = user;
        localStorage.setItem('auth_token', token);
    }

    clearAuth() {
        this.token = null;
        this.currentUser = null;
        localStorage.removeItem('auth_token');
    }

    clearOAuthState() {
        sessionStorage.removeItem('oauth_state');
    }

    logout() {
        this.clearAuth();
        // Reset to light mode on logout for new visitors
        if (window.themeManager) {
            window.themeManager.applyTheme('light');
        }
        this.showNotification('Logged out successfully', 'success');
        this.showAuthScreen();
    }

    toggleUserMenu() {
        const dropdown = document.getElementById('user-dropdown');
        const isVisible = dropdown.style.display === 'block';
        dropdown.style.display = isVisible ? 'none' : 'block';
    }

    closeUserMenu() {
        document.getElementById('user-dropdown').style.display = 'none';
    }

    setLoading(loading) {
        const buttons = document.querySelectorAll('.auth-form button[type="submit"], .btn-google');
        buttons.forEach(button => {
            if (loading) {
                button.disabled = true;
                button.style.opacity = '0.6';
                const originalText = button.innerHTML;
                button.dataset.originalText = originalText;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            } else {
                button.disabled = false;
                button.style.opacity = '1';
                if (button.dataset.originalText) {
                    button.innerHTML = button.dataset.originalText;
                    delete button.dataset.originalText;
                }
            }
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const messageEl = document.getElementById('notification-message');
        
        messageEl.textContent = message;
        notification.className = `notification notification-${type}`;
        notification.style.display = 'block';

        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.style.display = 'none';
        }, 5000);

        // Close button
        document.getElementById('notification-close').onclick = () => {
            notification.style.display = 'none';
        };
    }

    // Get current user info
    getCurrentUser() {
        return this.currentUser;
    }

    // Get auth token for API calls
    getAuthToken() {
        return this.token;
    }

    // Make authenticated API calls
    async authenticatedFetch(url, options = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return fetch(url, {
            ...options,
            headers,
            credentials: 'include'  // This ensures cookies are sent with the request
        });
    }
}

// Initialize auth manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.authManager = new AuthManager();
    
    // Check for OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('code') && urlParams.get('state')) {
        window.authManager.handleOAuthCallback();
    }
});
