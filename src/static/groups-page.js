/**
 * Groups Management Page JavaScript
 * 
 * Handles all functionality for the dedicated groups management page
 */

class GroupsPage {
    constructor() {
        this.groups = [];
        this.currentGroup = null;
        this.init();
    }

    init() {
        this.checkAuth();
        this.loadGroups();
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

    bindEvents() {
        // Create group button
        document.getElementById('create-group-btn').addEventListener('click', () => {
            this.showCreateGroupModal();
        });

        // Modal controls
        document.getElementById('create-group-close').addEventListener('click', () => {
            this.hideCreateGroupModal();
        });

        document.getElementById('cancel-create-group').addEventListener('click', () => {
            this.hideCreateGroupModal();
        });

        // Form submission
        document.getElementById('create-group-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createGroup();
        });

        // Group details navigation
        document.getElementById('back-to-groups-btn').addEventListener('click', () => {
            this.showGroupsList();
        });

        document.getElementById('create-group-board-btn').addEventListener('click', () => {
            this.createGroupBoard();
        });

        // User menu is handled by auth.js - no duplicate handlers needed

        // Close modal when clicking outside
        document.getElementById('create-group-modal').addEventListener('click', (e) => {
            if (e.target.id === 'create-group-modal') {
                this.hideCreateGroupModal();
            }
        });
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

    async loadGroups() {
        try {
            const response = await fetch('/api/groups/', {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to load groups');
            }

            this.groups = await response.json();
            this.renderGroups();
        } catch (error) {
            console.error('Error loading groups:', error);
            this.showError('Failed to load groups');
        }
    }

    renderGroups() {
        const container = document.getElementById('groups-container');
        
        if (this.groups.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <h3>No groups yet</h3>
                    <p>Create your first group to start collaborating with others</p>
                    <button class="btn btn-primary" onclick="groupsPage.showCreateGroupModal()">
                        <i class="fas fa-plus"></i>
                        Create Your First Group
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="groups-grid">
                ${this.groups.map(group => `
                    <div class="group-card" data-group-id="${group.id}">
                        <div class="group-card-header">
                            <h3>${this.escapeHtml(group.name)}</h3>
                            <span class="role-badge role-${group.user_role}">${group.user_role}</span>
                        </div>
                        <p class="group-description">${this.escapeHtml(group.description || 'No description')}</p>
                        <div class="group-stats">
                            <div class="stat">
                                <i class="fas fa-users"></i>
                                ${group.member_count} members
                            </div>
                            <div class="stat">
                                <i class="fas fa-calendar"></i>
                                ${this.formatDate(group.created_at)}
                            </div>
                        </div>
                        <div class="group-actions">
                            <button class="btn btn-primary btn-sm" onclick="groupsPage.viewGroup(${group.id})">
                                <i class="fas fa-eye"></i>
                                View Details
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async viewGroup(groupId) {
        try {
            const response = await fetch(`/api/groups/${groupId}`, {
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load group details');
            }

            this.currentGroup = await response.json();
            this.showGroupDetails();
        } catch (error) {
            console.error('Error loading group details:', error);
            this.showError('Failed to load group details');
        }
    }

    showGroupDetails() {
        const group = this.currentGroup;
        
        // Update header
        document.getElementById('group-details-title').textContent = group.name;
        document.getElementById('group-details-description').textContent = group.description || 'No description';
        
        // Update stats
        document.getElementById('member-count').textContent = group.member_count;
        document.getElementById('group-created').textContent = this.formatDate(group.created_at);
        
        // Find user's role
        const userRole = this.groups.find(g => g.id === group.id)?.user_role || 'member';
        const roleElement = document.getElementById('user-role');
        roleElement.textContent = userRole;
        roleElement.className = `role-badge role-${userRole}`;

        // Render members
        this.renderMembers(group.members);
        
        // Load group boards
        this.loadGroupBoards(group.id);

        // Show details section
        document.getElementById('groups-container').parentElement.style.display = 'none';
        document.getElementById('group-details-section').style.display = 'block';
    }

    renderMembers(members) {
        const container = document.getElementById('members-list');
        
        container.innerHTML = members.map(member => `
            <div class="member-card">
                <div class="member-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="member-info">
                    <div class="member-name">${this.escapeHtml(member.user.full_name || member.user.username)}</div>
                    <div class="member-email">${this.escapeHtml(member.user.email)}</div>
                </div>
                <div class="member-role">
                    <span class="role-badge role-${member.role}">${member.role}</span>
                </div>
            </div>
        `).join('');
    }

    async loadGroupBoards(groupId) {
        try {
            const response = await fetch('/api/boards/', {
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load boards');
            }

            const allBoards = await response.json();
            const groupBoards = allBoards.filter(board => board.group_id === groupId);
            this.renderGroupBoards(groupBoards);
        } catch (error) {
            console.error('Error loading group boards:', error);
            document.getElementById('group-boards-list').innerHTML = `
                <div class="error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    Failed to load boards
                </div>
            `;
        }
    }

    renderGroupBoards(boards) {
        const container = document.getElementById('group-boards-list');
        
        if (boards.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clipboard"></i>
                    <p>No boards yet</p>
                    <button class="btn btn-primary btn-sm" onclick="groupsPage.createGroupBoard()">
                        <i class="fas fa-plus"></i>
                        Create First Board
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = boards.map(board => `
            <div class="board-card">
                <h4>${this.escapeHtml(board.name)}</h4>
                <p>${this.escapeHtml(board.description || 'No description')}</p>
                <div class="board-meta">
                    <span><i class="fas fa-calendar"></i> ${this.formatDate(board.created_at)}</span>
                </div>
                <div class="board-actions">
                    <a href="/?board=${board.id}" class="btn btn-primary btn-sm">
                        <i class="fas fa-external-link-alt"></i>
                        Open Board
                    </a>
                </div>
            </div>
        `).join('');
    }

    showGroupsList() {
        document.getElementById('group-details-section').style.display = 'none';
        document.getElementById('groups-container').parentElement.style.display = 'block';
        this.currentGroup = null;
    }

    showCreateGroupModal() {
        document.getElementById('create-group-modal').style.display = 'block';
    }

    hideCreateGroupModal() {
        document.getElementById('create-group-modal').style.display = 'none';
        document.getElementById('create-group-form').reset();
    }

    async createGroup() {
        const form = document.getElementById('create-group-form');
        const formData = new FormData(form);
        
        const groupData = {
            name: formData.get('name'),
            description: formData.get('description') || null
        };

        try {
            const response = await fetch('/api/groups/', {
                method: 'POST',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(groupData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create group');
            }

            const newGroup = await response.json();
            this.showSuccess(`Group "${newGroup.name}" created successfully!`);
            this.hideCreateGroupModal();
            await this.loadGroups();
        } catch (error) {
            console.error('Error creating group:', error);
            this.showError(error.message);
        }
    }

    async createGroupBoard() {
        if (!this.currentGroup) return;

        const boardName = prompt(`Enter name for the new board in "${this.currentGroup.name}":`);
        if (!boardName) return;

        try {
            const response = await fetch('/api/boards/', {
                method: 'POST',
                headers: {
                    ...this.getAuthHeaders(),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: boardName,
                    description: `Board for ${this.currentGroup.name} group`,
                    group_id: this.currentGroup.id
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create board');
            }

            const newBoard = await response.json();
            this.showSuccess(`Board "${newBoard.name}" created successfully!`);
            
            // Refresh group boards
            this.loadGroupBoards(this.currentGroup.id);
        } catch (error) {
            console.error('Error creating group board:', error);
            this.showError(error.message);
        }
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

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.groupsPage = new GroupsPage();
});
