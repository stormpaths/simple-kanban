/**
 * API Keys Management JavaScript
 * 
 * Handles the UI and functionality for managing API keys including:
 * - Viewing existing API keys
 * - Creating new API keys
 * - Updating API key status
 * - Deleting API keys
 */

class ApiKeysManager {
    constructor() {
        this.apiKeys = [];
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        // Main API Keys menu item
        const apiKeysMenu = document.getElementById('api-keys-menu');
        if (apiKeysMenu) {
            apiKeysMenu.addEventListener('click', (e) => {
                e.preventDefault();
                this.openApiKeysModal();
            });
        }

        // Modal close events
        this.bindModalCloseEvents();

        // Create API key events
        this.bindCreateApiKeyEvents();

        // API key created modal events
        this.bindApiKeyCreatedEvents();
    }

    bindModalCloseEvents() {
        // API Keys modal close
        const apiKeysModalClose = document.getElementById('api-keys-modal-close');
        if (apiKeysModalClose) {
            apiKeysModalClose.addEventListener('click', () => {
                this.closeModal('api-keys-modal');
            });
        }

        // Create API key modal close
        const createModalClose = document.getElementById('create-api-key-modal-close');
        if (createModalClose) {
            createModalClose.addEventListener('click', () => {
                this.closeModal('create-api-key-modal');
            });
        }

        // API key created modal close
        const createdModalClose = document.getElementById('api-key-created-modal-close');
        if (createdModalClose) {
            createdModalClose.addEventListener('click', () => {
                this.closeModal('api-key-created-modal');
            });
        }

        // Close modals when clicking outside
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });
    }

    bindCreateApiKeyEvents() {
        // Create new key button
        const createBtn = document.getElementById('create-api-key-btn');
        if (createBtn) {
            createBtn.addEventListener('click', () => {
                this.openCreateApiKeyModal();
            });
        }

        // Cancel create
        const cancelBtn = document.getElementById('create-api-key-cancel');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.closeModal('create-api-key-modal');
            });
        }

        // Submit create form
        const createForm = document.getElementById('create-api-key-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createApiKey();
            });
        }
    }

    bindApiKeyCreatedEvents() {
        // Copy API key button
        const copyBtn = document.getElementById('copy-api-key-btn');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                this.copyApiKey();
            });
        }

        // Done button
        const doneBtn = document.getElementById('api-key-created-done');
        if (doneBtn) {
            doneBtn.addEventListener('click', () => {
                this.closeModal('api-key-created-modal');
                this.loadApiKeys(); // Refresh the list
            });
        }
    }

    async openApiKeysModal() {
        this.showModal('api-keys-modal');
        await this.loadApiKeys();
    }

    async loadApiKeys() {
        const loadingElement = document.getElementById('api-keys-loading');
        const listElement = document.getElementById('api-keys-list');
        
        if (loadingElement) loadingElement.style.display = 'block';

        try {
            const response = await this.authenticatedFetch('/api/api-keys/');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.apiKeys = data.api_keys || [];
            this.renderApiKeys();

        } catch (error) {
            console.error('Error loading API keys:', error);
            this.showError('Failed to load API keys. Please try again.');
        } finally {
            if (loadingElement) loadingElement.style.display = 'none';
        }
    }

    renderApiKeys() {
        const listElement = document.getElementById('api-keys-list');
        if (!listElement) return;

        if (this.apiKeys.length === 0) {
            listElement.innerHTML = `
                <div class="api-key-empty">
                    <i class="fas fa-key"></i>
                    <h4>No API Keys</h4>
                    <p>You haven't created any API keys yet. Create your first API key to get started.</p>
                </div>
            `;
            return;
        }

        const html = this.apiKeys.map(key => this.renderApiKeyItem(key)).join('');
        listElement.innerHTML = html;

        // Bind action events
        this.bindApiKeyActions();
    }

    renderApiKeyItem(apiKey) {
        const status = this.getKeyStatus(apiKey);
        const expiresText = apiKey.expires_at 
            ? new Date(apiKey.expires_at).toLocaleDateString()
            : 'Never';
        const lastUsedText = apiKey.last_used_at
            ? new Date(apiKey.last_used_at).toLocaleDateString()
            : 'Never';

        const scopeBadges = apiKey.scopes.map(scope => 
            `<span class="scope-badge ${scope}">${scope}</span>`
        ).join('');

        return `
            <div class="api-key-item" data-key-id="${apiKey.id}">
                <div class="api-key-header">
                    <div class="api-key-info">
                        <h5>${this.escapeHtml(apiKey.name)}</h5>
                        <div class="api-key-prefix">${apiKey.key_prefix}...</div>
                    </div>
                    <div class="api-key-actions">
                        <button class="btn btn-secondary" onclick="apiKeysManager.toggleApiKey(${apiKey.id}, ${!apiKey.is_active})">
                            <i class="fas fa-${apiKey.is_active ? 'pause' : 'play'}"></i>
                            ${apiKey.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button class="btn btn-danger" onclick="apiKeysManager.deleteApiKey(${apiKey.id})">
                            <i class="fas fa-trash"></i>
                            Delete
                        </button>
                    </div>
                </div>
                
                <div class="api-key-details">
                    <div class="detail-item">
                        <div class="detail-label">Status</div>
                        <div class="detail-value">
                            <span class="api-key-status status-${status.class}">
                                <span class="status-indicator"></span>
                                ${status.text}
                            </span>
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Scopes</div>
                        <div class="detail-value">
                            <div class="api-key-scopes">${scopeBadges}</div>
                        </div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Expires</div>
                        <div class="detail-value">${expiresText}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Last Used</div>
                        <div class="detail-value">${lastUsedText}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Usage Count</div>
                        <div class="detail-value">${apiKey.usage_count}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Created</div>
                        <div class="detail-value">${new Date(apiKey.created_at).toLocaleDateString()}</div>
                    </div>
                </div>
                
                ${apiKey.description ? `<div class="api-key-description">${this.escapeHtml(apiKey.description)}</div>` : ''}
            </div>
        `;
    }

    getKeyStatus(apiKey) {
        if (!apiKey.is_active) {
            return { class: 'inactive', text: 'Inactive' };
        }
        
        if (apiKey.expires_at && new Date(apiKey.expires_at) < new Date()) {
            return { class: 'expired', text: 'Expired' };
        }
        
        return { class: 'active', text: 'Active' };
    }

    bindApiKeyActions() {
        // Actions are bound via onclick attributes in the HTML
        // This is simpler for dynamic content
    }

    openCreateApiKeyModal() {
        this.showModal('create-api-key-modal');
        this.resetCreateForm();
    }

    resetCreateForm() {
        const form = document.getElementById('create-api-key-form');
        if (form) {
            form.reset();
            // Check the 'read' scope by default
            const readCheckbox = form.querySelector('input[value="read"]');
            if (readCheckbox) readCheckbox.checked = true;
        }
    }

    async createApiKey() {
        const form = document.getElementById('create-api-key-form');
        if (!form) return;

        const formData = new FormData(form);
        const scopes = Array.from(form.querySelectorAll('input[name="scopes"]:checked'))
            .map(cb => cb.value);

        if (scopes.length === 0) {
            this.showError('Please select at least one scope.');
            return;
        }

        const data = {
            name: formData.get('name'),
            description: formData.get('description') || null,
            scopes: scopes,
            expires_in_days: formData.get('expires_in_days') ? parseInt(formData.get('expires_in_days')) : null
        };

        const submitBtn = document.getElementById('create-api-key-submit');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating...';
        }

        try {
            const response = await this.authenticatedFetch('/api/api-keys/', {
                method: 'POST',
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const result = await response.json();
            this.showApiKeyCreated(result);
            this.closeModal('create-api-key-modal');

        } catch (error) {
            console.error('Error creating API key:', error);
            this.showError(`Failed to create API key: ${error.message}`);
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Create API Key';
            }
        }
    }

    showApiKeyCreated(result) {
        const { api_key, key_info } = result;
        
        // Populate the created modal
        document.getElementById('created-api-key-value').value = api_key;
        document.getElementById('created-key-name').textContent = key_info.name;
        document.getElementById('created-key-scopes').textContent = key_info.scopes.join(', ');
        document.getElementById('created-key-expires').textContent = 
            key_info.expires_at ? new Date(key_info.expires_at).toLocaleDateString() : 'Never';
        
        this.showModal('api-key-created-modal');
    }

    async copyApiKey() {
        const input = document.getElementById('created-api-key-value');
        if (!input) return;

        try {
            await navigator.clipboard.writeText(input.value);
            
            const btn = document.getElementById('copy-api-key-btn');
            if (btn) {
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i>';
                btn.classList.add('btn-success');
                
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                    btn.classList.remove('btn-success');
                }, 2000);
            }
            
            this.showSuccess('API key copied to clipboard!');
        } catch (error) {
            console.error('Failed to copy API key:', error);
            // Fallback: select the text
            input.select();
            input.setSelectionRange(0, 99999);
            this.showError('Please copy the API key manually.');
        }
    }

    async toggleApiKey(keyId, enable) {
        try {
            const response = await this.authenticatedFetch(`/api/api-keys/${keyId}`, {
                method: 'PUT',
                body: JSON.stringify({ is_active: enable })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            this.showSuccess(`API key ${enable ? 'enabled' : 'disabled'} successfully.`);
            await this.loadApiKeys();

        } catch (error) {
            console.error('Error toggling API key:', error);
            this.showError('Failed to update API key status.');
        }
    }

    async deleteApiKey(keyId) {
        if (!confirm('Are you sure you want to delete this API key? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await this.authenticatedFetch(`/api/api-keys/${keyId}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            this.showSuccess('API key deleted successfully.');
            await this.loadApiKeys();

        } catch (error) {
            console.error('Error deleting API key:', error);
            this.showError('Failed to delete API key.');
        }
    }

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        }
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'success') {
        // Try to use the global kanban app's notification system
        if (window.kanbanApp && window.kanbanApp.showNotification) {
            window.kanbanApp.showNotification(message, type);
            return;
        }

        // Fallback: implement our own notification system
        const notification = document.getElementById('notification');
        const messageEl = document.getElementById('notification-message');
        
        if (!notification || !messageEl) {
            // Ultimate fallback: use alert
            alert(message);
            return;
        }

        messageEl.textContent = message;
        notification.className = `notification ${type === 'error' ? 'notification-error' : 'notification-success'}`;
        notification.classList.add('show');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.remove('show');
        }, 5000);
    }

    async authenticatedFetch(url, options = {}) {
        // Use the global auth manager if available
        if (window.authManager && window.authManager.authenticatedFetch) {
            return await window.authManager.authenticatedFetch(url, options);
        }

        // Fallback: try to get token manually
        const token = this.getAuthToken();
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        return fetch(url, {
            ...options,
            headers,
            credentials: 'include'
        });
    }

    getAuthToken() {
        // Try to get from global auth manager first
        if (window.authManager && window.authManager.token) {
            return window.authManager.token;
        }

        // Fallback: try localStorage
        const token = localStorage.getItem('access_token');
        if (token) return token;
        
        // Fallback: try cookies
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'access_token') {
                return value;
            }
        }
        
        return null;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the API Keys Manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.apiKeysManager = new ApiKeysManager();
});
