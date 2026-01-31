/**
 * API Keys Management Page JavaScript
 * 
 * Handles all functionality for the dedicated API keys management page
 */

class ApiKeysPage {
    constructor() {
        this.apiKeys = [];
        this.init();
    }

    async init() {
        this.checkAuth();
        console.log('API Keys page initializing...');
        await this.loadApiKeys();
        console.log('About to load stats on init...');
        await this.loadStats();
        console.log('Stats loaded on init.');
        // Delay event binding to ensure DOM is ready
        setTimeout(() => {
            this.bindEvents();
        }, 100);
    }

    async checkAuth() {
        // Try multiple token sources - prioritize 'token' like admin page
        const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
        
        if (!token) {
            // Try to check if we're authenticated via cookies by making an API call
            try {
                const response = await fetch('/api/auth/me');
                if (response.ok) {
                    const user = await response.json();
                    this.setUserInfo(user);
                    return; // We're authenticated via cookies
                }
            } catch (error) {
                console.log('No cookie auth available');
            }
            
            // No authentication found, redirect
            window.location.href = '/';
            return;
        }
        
        // We have a token, verify it works
        try {
            const response = await fetch('/api/auth/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const user = await response.json();
                this.setUserInfo(user);
                return;
            }
        } catch (error) {
            console.error('Token verification failed:', error);
        }
        
        // Token is invalid, redirect
        window.location.href = '/';
    }
    
    setUserInfo(user) {
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) {
            // Use same logic as main app: full_name || username || 'User'
            userNameEl.textContent = user.full_name || user.username || 'User';
        }
        
        // Show admin panel link for admin users
        const adminPanel = document.getElementById('admin-panel');
        if (adminPanel) {
            if (user.id === 1 || user.is_admin) {
                adminPanel.style.display = 'block';
            } else {
                adminPanel.style.display = 'none';
            }
        }
    }
    
    getAuthHeaders() {
        const token = localStorage.getItem('token') || localStorage.getItem('auth_token');
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    }

    bindEvents() {
        // Create API key button
        document.getElementById('create-api-key-btn').addEventListener('click', () => {
            this.showCreateApiKeyModal();
        });

        // Modal controls
        document.getElementById('create-api-key-close').addEventListener('click', () => {
            this.hideCreateApiKeyModal();
        });

        document.getElementById('cancel-create-api-key').addEventListener('click', () => {
            this.hideCreateApiKeyModal();
        });

        // Form submission
        document.getElementById('create-api-key-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createApiKey();
        });

        // User menu is handled by auth.js - no duplicate handlers needed

        // Close modal when clicking outside
        document.getElementById('create-api-key-modal').addEventListener('click', (e) => {
            if (e.target.id === 'create-api-key-modal') {
                this.hideCreateApiKeyModal();
            }
        });
    }

    async loadApiKeys() {
        try {
            const response = await fetch('/api/api-keys/', {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to load API keys');
            }

            const data = await response.json();
            console.log('API Keys response:', data);
            
            // Handle the response format: { api_keys: [...], total: N }
            if (data && Array.isArray(data.api_keys)) {
                this.apiKeys = data.api_keys;
            } else if (Array.isArray(data)) {
                this.apiKeys = data;
            } else {
                this.apiKeys = [];
            }
            
            console.log('Loaded API keys:', this.apiKeys);
            this.renderApiKeys();
        } catch (error) {
            console.error('Error loading API keys:', error);
            this.showApiKeysError('Failed to load API keys');
        }
    }

    renderApiKeys() {
        const container = document.getElementById('api-keys-container');
        console.log('renderApiKeys called with:', this.apiKeys);
        console.log('Container element found:', !!container);
        
        if (!Array.isArray(this.apiKeys) || this.apiKeys.length === 0) {
            console.log('Showing empty state - no API keys');
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-key"></i>
                    <h3>No API keys yet</h3>
                    <p>Create your first API key to start using the Simple Kanban API</p>
                    <button class="btn btn-primary" onclick="apiKeysPage.showCreateApiKeyModal()">
                        <i class="fas fa-plus"></i>
                        Create Your First API Key
                    </button>
                </div>
            `;
            return;
        }

        console.log('Rendering API keys grid with', this.apiKeys.length, 'keys');
        
        container.innerHTML = `
            <div class="api-keys-grid">
                ${this.apiKeys.map(key => {
                    console.log('Rendering key:', key);
                    return `
                    <div class="api-key-card" data-key-id="${key.id}">
                        <div class="api-key-header">
                            <h3>${this.escapeHtml(key.name)}</h3>
                            <span class="key-status ${key.is_active ? 'active' : 'inactive'}">
                                ${key.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        <p class="api-key-description">${this.escapeHtml(key.description || 'No description')}</p>
                        <div class="api-key-details">
                            <div class="key-detail">
                                <strong>Key:</strong> 
                                <code class="api-key-value">${key.key_prefix}...</code>
                                <span class="key-hint" title="Full key only shown at creation">(hidden)</span>
                            </div>
                            <div class="key-detail">
                                <strong>Created:</strong> ${this.formatDate(key.created_at)}
                            </div>
                            ${key.expires_at ? `
                                <div class="key-detail">
                                    <strong>Expires:</strong> ${this.formatDate(key.expires_at)}
                                </div>
                            ` : ''}
                        </div>
                        <div class="api-key-actions">
                            <button class="btn btn-sm btn-secondary" onclick="apiKeysPage.toggleApiKey('${key.id}')">
                                <i class="fas fa-${key.is_active ? 'pause' : 'play'}"></i>
                                ${key.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="apiKeysPage.deleteApiKey('${key.id}')">
                                <i class="fas fa-trash"></i>
                                Delete
                            </button>
                        </div>
                    </div>
                `;
                }).join('')}
            </div>
        `;
    }

    async loadStats() {
        try {
            console.log('Loading API key usage statistics...');
            const response = await fetch('/api/api-keys/stats/usage', {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to load API key statistics');
            }

            const stats = await response.json();
            console.log('Loaded stats:', stats);
            
            // Transform the API response to match our UI format
            const uiStats = {
                total_keys: stats.total_keys || 0,
                active_keys: stats.active_keys || 0,
                expired_keys: stats.expired_keys || 0,
                total_requests: stats.total_requests || 0,
                requests_today: stats.requests_today || 0,
                most_used_key: stats.most_used_key || null
            };
            
            this.renderStats(uiStats);
        } catch (error) {
            console.error('Error loading stats:', error);
            this.showStatsError('Failed to load statistics');
        }
    }

    renderStats(stats) {
        const container = document.getElementById('api-stats-container');
        
        container.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-key"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.total_keys}</div>
                        <div class="stat-label">Total API Keys</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-check-circle"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.active_keys}</div>
                        <div class="stat-label">Active Keys</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-chart-line"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.total_requests}</div>
                        <div class="stat-label">Total Requests</div>
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-icon">
                        <i class="fas fa-calendar-day"></i>
                    </div>
                    <div class="stat-content">
                        <div class="stat-number">${stats.requests_today}</div>
                        <div class="stat-label">Requests Today</div>
                    </div>
                </div>
            </div>
        `;
    }

    showCreateApiKeyModal() {
        document.getElementById('create-api-key-modal').style.display = 'block';
    }

    hideCreateApiKeyModal() {
        document.getElementById('create-api-key-modal').style.display = 'none';
        document.getElementById('create-api-key-form').reset();
    }

    async createApiKey() {
        const form = document.getElementById('create-api-key-form');
        const submitBtn = form.querySelector('button[type="submit"]');
        
        // Prevent double-clicks
        if (submitBtn.disabled) return;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        
        const formData = new FormData(form);
        
        const scopes = Array.from(form.querySelectorAll('input[name="scopes"]:checked'))
            .map(input => input.value);
        
        const apiKeyData = {
            name: formData.get('name'),
            description: formData.get('description') || null,
            scopes: scopes,
            expires_in_days: formData.get('expires_in_days') ? parseInt(formData.get('expires_in_days')) : null
        };

        try {
            const response = await fetch('/api/api-keys/', {
                method: 'POST',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(apiKeyData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create API key');
            }

            const result = await response.json();
            
            // Close the create modal
            this.hideCreateApiKeyModal();
            
            // Show the newly created key in a special dialog
            // The full key is only shown ONCE - user must copy it now!
            this.showNewKeyDialog(result.api_key, result.key_info || result);
            
            // Reload the keys list and stats
            await Promise.all([this.loadApiKeys(), this.loadStats()]);
        } catch (error) {
            console.error('Error creating API key:', error);
            this.showError(error.message);
        } finally {
            // Re-enable the submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-plus"></i> Create API Key';
        }
    }
    
    showNewKeyDialog(fullKey, keyInfo) {
        // Store the full key temporarily for copying
        this.newlyCreatedKey = fullKey;
        
        // Create and show the new key dialog
        let dialog = document.getElementById('new-key-dialog');
        if (!dialog) {
            dialog = document.createElement('div');
            dialog.id = 'new-key-dialog';
            dialog.className = 'modal';
            document.body.appendChild(dialog);
        }
        
        dialog.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3><i class="fas fa-check-circle" style="color: #10b981;"></i> API Key Created!</h3>
                </div>
                <div class="modal-body">
                    <div class="new-key-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        <strong>Important:</strong> Copy your API key now. You won't be able to see it again!
                    </div>
                    <div class="form-group">
                        <label>Your API Key</label>
                        <div class="new-key-display">
                            <code id="new-key-value">${this.escapeHtml(fullKey)}</code>
                            <button class="btn btn-primary copy-new-key-btn" onclick="apiKeysPage.copyNewKey()">
                                <i class="fas fa-copy"></i> Copy
                            </button>
                        </div>
                    </div>
                    <div class="key-details-summary">
                        <p><strong>Name:</strong> ${this.escapeHtml(keyInfo.name)}</p>
                        ${keyInfo.expires_at ? `<p><strong>Expires:</strong> ${this.formatDate(keyInfo.expires_at)}</p>` : '<p><strong>Expires:</strong> Never</p>'}
                    </div>
                    <div class="form-actions">
                        <button class="btn btn-secondary" onclick="apiKeysPage.closeNewKeyDialog()">
                            I've copied the key
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        dialog.style.display = 'block';
        
        // Add styles for the new key dialog if not already present
        if (!document.getElementById('new-key-dialog-styles')) {
            const styles = document.createElement('style');
            styles.id = 'new-key-dialog-styles';
            styles.textContent = `
                .new-key-warning {
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin-bottom: 20px;
                    color: #92400e;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .new-key-warning i {
                    color: #f59e0b;
                    font-size: 1.2em;
                }
                [data-theme="dark"] .new-key-warning {
                    background: #451a03;
                    border-color: #b45309;
                    color: #fcd34d;
                }
                .new-key-display {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    background: var(--bg-secondary, #f3f4f6);
                    border: 1px solid var(--border-primary, #e5e7eb);
                    border-radius: 8px;
                    padding: 12px;
                }
                .new-key-display code {
                    flex: 1;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    word-break: break-all;
                    background: transparent;
                    padding: 0;
                }
                .copy-new-key-btn {
                    white-space: nowrap;
                }
                .key-details-summary {
                    margin: 16px 0;
                    padding: 12px;
                    background: var(--bg-secondary, #f9fafb);
                    border-radius: 8px;
                }
                .key-details-summary p {
                    margin: 4px 0;
                }
                .key-hint {
                    color: var(--text-muted, #9ca3af);
                    font-size: 0.85em;
                    font-style: italic;
                    margin-left: 4px;
                }
                .btn-success {
                    background: #10b981 !important;
                    border-color: #10b981 !important;
                }
            `;
            document.head.appendChild(styles);
        }
    }
    
    copyNewKey() {
        if (!this.newlyCreatedKey) return;
        
        navigator.clipboard.writeText(this.newlyCreatedKey).then(() => {
            const btn = document.querySelector('.copy-new-key-btn');
            if (btn) {
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btn.classList.add('btn-success');
                setTimeout(() => {
                    btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    btn.classList.remove('btn-success');
                }, 2000);
            }
            this.showSuccess('API key copied to clipboard!');
        }).catch(() => {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = this.newlyCreatedKey;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            this.showSuccess('API key copied to clipboard!');
        });
    }
    
    closeNewKeyDialog() {
        const dialog = document.getElementById('new-key-dialog');
        if (dialog) {
            dialog.style.display = 'none';
        }
        this.newlyCreatedKey = null; // Clear the key from memory
    }
    async copyApiKey(keyId) {
        // The full key is only available at creation time
        // Show a message explaining this security feature
        this.showError('API keys can only be copied when first created. For security, the full key is not stored.');
    }

    async toggleApiKey(keyId) {
        try {
            const response = await fetch(`/api/api-keys/${keyId}/toggle`, {
                method: 'POST',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to toggle API key');
            }

            this.showSuccess('API key status updated!');
            await this.loadApiKeys();
            await this.loadStats();
        } catch (error) {
            console.error('Error toggling API key:', error);
            this.showError(error.message);
        }
    }

    async deleteApiKey(keyId) {
        if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/api-keys/${keyId}`, {
                method: 'DELETE',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to delete API key');
            }

            this.showSuccess('API key deleted successfully!');
            await this.loadApiKeys();
            await this.loadStats();
        } catch (error) {
            console.error('Error deleting API key:', error);
            this.showError(error.message);
        }
    }

    showApiKeysError(message) {
        document.getElementById('api-keys-container').innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
                <button class="btn btn-primary" onclick="apiKeysPage.loadApiKeys()">
                    <i class="fas fa-refresh"></i>
                    Retry
                </button>
            </div>
        `;
    }

    showStatsError(message) {
        document.getElementById('api-stats-container').innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
            </div>
        `;
    }

    // User menu methods removed - handled by auth.js

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
        window.location.href = '/';
    }

    // Utility methods
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString();
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.getElementById('notification');
        const messageEl = document.getElementById('notification-message');
        
        messageEl.textContent = message;
        notification.className = `notification ${type}`;
        notification.style.display = 'block';
        
        setTimeout(() => {
            notification.style.display = 'none';
        }, 5000);
        
        document.getElementById('notification-close').onclick = () => {
            notification.style.display = 'none';
        };
    }
}

// Copy to clipboard utility
function copyToClipboard(button) {
    const codeBlock = button.parentElement.querySelector('code');
    const text = codeBlock.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        button.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i>';
        }, 2000);
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        button.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => {
            button.innerHTML = '<i class="fas fa-copy"></i>';
        }, 2000);
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.apiKeysPage = new ApiKeysPage();
});
