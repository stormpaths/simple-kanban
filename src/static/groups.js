/**
 * Group Management Interface for Simple Kanban Board
 * 
 * Provides functionality for:
 * - Creating and managing groups
 * - Adding/removing group members
 * - Creating group-owned boards
 * - Managing group permissions
 */

class GroupManager {
    constructor() {
        this.groups = [];
        this.currentGroup = null;
        this.init();
    }

    init() {
        this.createGroupsModal();
        this.bindEvents();
    }

    createGroupsModal() {
        const modal = document.createElement('div');
        modal.id = 'groups-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content groups-modal-content">
                <div class="modal-header">
                    <h2><i class="fas fa-users"></i> Group Management</h2>
                    <button class="modal-close" id="groups-modal-close">&times;</button>
                </div>
                
                <div class="modal-body">
                    <!-- Groups List Section -->
                    <div class="groups-section">
                        <div class="section-header">
                            <h3>Your Groups</h3>
                            <button class="btn btn-primary btn-sm" id="create-group-btn">
                                <i class="fas fa-plus"></i> Create Group
                            </button>
                        </div>
                        
                        <div id="groups-list" class="groups-list">
                            <div class="loading-spinner">
                                <i class="fas fa-spinner fa-spin"></i> Loading groups...
                            </div>
                        </div>
                    </div>

                    <!-- Group Details Section -->
                    <div id="group-details" class="group-details" style="display: none;">
                        <div class="section-header">
                            <h3 id="group-details-title">Group Details</h3>
                            <div class="group-actions">
                                <button class="btn btn-secondary btn-sm" id="edit-group-btn">
                                    <i class="fas fa-edit"></i> Edit
                                </button>
                                <button class="btn btn-success btn-sm" id="create-group-board-btn">
                                    <i class="fas fa-plus"></i> Create Board
                                </button>
                                <button class="btn btn-danger btn-sm" id="delete-group-btn">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </div>
                        </div>
                        
                        <div class="group-info">
                            <p id="group-description"></p>
                            <div class="group-stats">
                                <span class="stat">
                                    <i class="fas fa-users"></i>
                                    <span id="member-count">0</span> members
                                </span>
                                <span class="stat">
                                    <i class="fas fa-calendar"></i>
                                    Created <span id="group-created"></span>
                                </span>
                            </div>
                        </div>

                        <div class="group-members">
                            <h4>Members</h4>
                            <div id="members-list" class="members-list"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }

    bindEvents() {
        // Note: groups-menu now links directly to /static/groups.html
        // No need to intercept clicks anymore

        document.getElementById('groups-modal-close').addEventListener('click', () => {
            this.hideGroupsModal();
        });

        // Group actions
        document.getElementById('create-group-btn').addEventListener('click', () => {
            this.showCreateGroupForm();
        });

        document.getElementById('edit-group-btn').addEventListener('click', () => {
            this.showEditGroupForm();
        });

        document.getElementById('delete-group-btn').addEventListener('click', () => {
            this.confirmDeleteGroup();
        });

        document.getElementById('create-group-board-btn').addEventListener('click', () => {
            this.createGroupBoard();
        });

        // Close modal when clicking outside
        document.getElementById('groups-modal').addEventListener('click', (e) => {
            if (e.target.id === 'groups-modal') {
                this.hideGroupsModal();
            }
        });
    }

    async showGroupsModal() {
        document.getElementById('groups-modal').style.display = 'block';
        await this.loadGroups();
    }

    hideGroupsModal() {
        document.getElementById('groups-modal').style.display = 'none';
        this.currentGroup = null;
        document.getElementById('group-details').style.display = 'none';
    }

    async loadGroups() {
        try {
            const response = await fetch('/api/groups/', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load groups');
            }

            this.groups = await response.json();
            this.renderGroupsList();
        } catch (error) {
            console.error('Error loading groups:', error);
            this.showError('Failed to load groups');
        }
    }

    renderGroupsList() {
        const groupsList = document.getElementById('groups-list');
        
        if (this.groups.length === 0) {
            groupsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-users"></i>
                    <p>No groups yet</p>
                    <p class="text-muted">Create your first group to start collaborating</p>
                </div>
            `;
            return;
        }

        groupsList.innerHTML = this.groups.map(group => `
            <div class="group-item" data-group-id="${group.id}">
                <div class="group-item-content">
                    <div class="group-item-header">
                        <h4>${this.escapeHtml(group.name)}</h4>
                        <span class="group-role role-${group.user_role}">${group.user_role}</span>
                    </div>
                    <p class="group-description">${this.escapeHtml(group.description || 'No description')}</p>
                    <div class="group-meta">
                        <span><i class="fas fa-users"></i> ${group.member_count} members</span>
                        <span><i class="fas fa-calendar"></i> ${this.formatDate(group.created_at)}</span>
                    </div>
                </div>
                <div class="group-item-actions">
                    <button class="btn btn-sm btn-secondary" onclick="groupManager.viewGroup(${group.id})">
                        <i class="fas fa-eye"></i> View
                    </button>
                </div>
            </div>
        `).join('');
    }

    async viewGroup(groupId) {
        try {
            const response = await fetch(`/api/groups/${groupId}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error('Failed to load group details');
            }

            this.currentGroup = await response.json();
            this.renderGroupDetails();
        } catch (error) {
            console.error('Error loading group details:', error);
            this.showError('Failed to load group details');
        }
    }

    renderGroupDetails() {
        const group = this.currentGroup;
        
        document.getElementById('group-details-title').textContent = group.name;
        document.getElementById('group-description').textContent = group.description || 'No description';
        document.getElementById('member-count').textContent = group.member_count;
        document.getElementById('group-created').textContent = this.formatDate(group.created_at);

        // Render members
        const membersList = document.getElementById('members-list');
        membersList.innerHTML = group.members.map(member => `
            <div class="member-item">
                <div class="member-info">
                    <div class="member-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="member-details">
                        <div class="member-name">${this.escapeHtml(member.user.full_name || member.user.username)}</div>
                        <div class="member-email">${this.escapeHtml(member.user.email)}</div>
                    </div>
                </div>
                <div class="member-role">
                    <span class="role-badge role-${member.role}">${member.role}</span>
                </div>
            </div>
        `).join('');

        document.getElementById('group-details').style.display = 'block';
    }

    showCreateGroupForm() {
        const formHtml = `
            <div class="create-group-form">
                <h3>Create New Group</h3>
                <form id="create-group-form">
                    <div class="form-group">
                        <label for="group-name">Group Name</label>
                        <input type="text" id="group-name" name="name" required 
                               placeholder="Enter group name" maxlength="255">
                    </div>
                    <div class="form-group">
                        <label for="group-description">Description (Optional)</label>
                        <textarea id="group-description" name="description" 
                                  placeholder="Describe the purpose of this group" 
                                  maxlength="1000" rows="3"></textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="groupManager.cancelCreateGroup()">
                            Cancel
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-plus"></i> Create Group
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.getElementById('groups-list').innerHTML = formHtml;
        
        document.getElementById('create-group-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createGroup();
        });
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
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
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
            await this.loadGroups(); // Refresh the list
        } catch (error) {
            console.error('Error creating group:', error);
            this.showError(error.message);
        }
    }

    cancelCreateGroup() {
        this.loadGroups(); // Go back to groups list
    }

    showEditGroupForm() {
        if (!this.currentGroup) {
            this.showError('No group selected');
            return;
        }

        const formHtml = `
            <div class="form-container">
                <h3><i class="fas fa-edit"></i> Edit Group</h3>
                <form id="edit-group-form">
                    <div class="form-group">
                        <label for="edit-group-name">Group Name</label>
                        <input type="text" id="edit-group-name" name="name" required 
                               placeholder="Enter group name" maxlength="255"
                               value="${this.escapeHtml(this.currentGroup.name)}">
                    </div>
                    <div class="form-group">
                        <label for="edit-group-description">Description (Optional)</label>
                        <textarea id="edit-group-description" name="description" 
                                  placeholder="Describe the purpose of this group" 
                                  maxlength="1000" rows="3">${this.escapeHtml(this.currentGroup.description || '')}</textarea>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn btn-secondary" onclick="groupManager.cancelEditGroup()">
                            Cancel
                        </button>
                        <button type="submit" class="btn btn-primary">
                            <i class="fas fa-save"></i> Save Changes
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.getElementById('groups-list').innerHTML = formHtml;
        
        document.getElementById('edit-group-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateGroup();
        });
    }

    async updateGroup() {
        if (!this.currentGroup) return;

        const form = document.getElementById('edit-group-form');
        const formData = new FormData(form);
        
        const groupData = {
            name: formData.get('name'),
            description: formData.get('description') || null
        };

        try {
            const response = await fetch(`/api/groups/${this.currentGroup.id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(groupData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update group');
            }

            const updatedGroup = await response.json();
            this.showSuccess(`Group "${updatedGroup.name}" updated successfully!`);
            this.currentGroup = updatedGroup;
            await this.loadGroups(); // Refresh the list
            this.showGroupDetails(updatedGroup); // Show updated details
        } catch (error) {
            console.error('Error updating group:', error);
            this.showError(error.message);
        }
    }

    cancelEditGroup() {
        if (this.currentGroup) {
            this.showGroupDetails(this.currentGroup); // Go back to group details
        } else {
            this.loadGroups(); // Go back to groups list
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    confirmDeleteGroup() {
        if (!this.currentGroup) {
            this.showError('No group selected');
            return;
        }

        const confirmMessage = `Are you sure you want to delete the group "${this.currentGroup.name}"?\n\nThis will:\n- Remove all members from the group\n- Unlink all group boards (boards will remain but become personal)\n- This action cannot be undone`;
        
        if (confirm(confirmMessage)) {
            this.deleteGroup();
        }
    }

    async deleteGroup() {
        if (!this.currentGroup) return;

        const groupId = this.currentGroup.id;
        const groupName = this.currentGroup.name;

        try {
            const response = await fetch(`/api/groups/${groupId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete group');
            }

            this.showSuccess(`Group "${groupName}" deleted successfully!`);
            this.currentGroup = null;
            document.getElementById('group-details').style.display = 'none';
            await this.loadGroups(); // Refresh the list
        } catch (error) {
            console.error('Error deleting group:', error);
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
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
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
            
            // Close modal and refresh boards
            this.hideGroupsModal();
            if (window.loadBoards) {
                window.loadBoards();
            }
        } catch (error) {
            console.error('Error creating group board:', error);
            this.showError(error.message);
        }
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
        // Use existing notification system if available
        if (window.showNotification) {
            window.showNotification(message, 'success');
        } else {
            alert(message);
        }
    }

    showError(message) {
        // Use existing notification system if available
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            alert('Error: ' + message);
        }
    }
}

// Initialize group manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.groupManager = new GroupManager();
});
