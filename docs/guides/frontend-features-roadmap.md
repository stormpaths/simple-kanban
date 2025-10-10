# 📋 Frontend Features TODO

**Last Updated:** October 9, 2025  
**Current Test Coverage:** 93% (57/61 tests passing)  
**Status:** 4 features need frontend implementation

---

## 🎯 Overview

The backend APIs are **100% complete and tested**. The following features need **frontend UI implementation only**:

| Feature | Backend API | Frontend UI | Priority | Effort |
|---------|-------------|-------------|----------|--------|
| Edit Group | ✅ Complete | ❌ Missing | High | 2-3 hours |
| Delete Group | ✅ Complete | ❌ Missing | Medium | 1-2 hours |
| Add Column | ✅ Complete | ❌ Missing | Medium | 2-3 hours |
| Manage Members | ✅ Complete | ❌ Missing | Low | 4-6 hours |

**Total Estimated Effort:** 9-14 hours

---

## 🔴 HIGH PRIORITY

### 1. Edit Group Functionality

**Status:** Button exists but does nothing  
**Files to Modify:** `src/static/groups.js`, `src/static/groups.html`  
**Estimated Time:** 2-3 hours

#### Current State
```javascript
// ✅ Button exists (line 56-58 in groups.js)
<button class="btn btn-secondary btn-sm" id="edit-group-btn">
    <i class="fas fa-edit"></i> Edit
</button>

// ❌ No event listener in bindEvents()
// ❌ No editGroup() method
// ❌ No edit modal/form
```

#### What's Needed

**Step 1: Add Event Listener** (5 min)
```javascript
// In bindEvents() method around line 100
document.getElementById('edit-group-btn').addEventListener('click', () => {
    this.showEditGroupForm();
});
```

**Step 2: Create Edit Form Modal** (30 min)
```javascript
showEditGroupForm() {
    if (!this.currentGroup) return;
    
    // Create modal similar to create form
    const modal = document.createElement('div');
    modal.id = 'edit-group-modal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Edit Group</h2>
                <button class="modal-close" id="edit-group-modal-close">&times;</button>
            </div>
            <form id="edit-group-form">
                <div class="form-group">
                    <label for="edit-group-name">Group Name</label>
                    <input type="text" id="edit-group-name" 
                           value="${this.escapeHtml(this.currentGroup.name)}" required>
                </div>
                <div class="form-group">
                    <label for="edit-group-description">Description</label>
                    <textarea id="edit-group-description">${this.escapeHtml(this.currentGroup.description || '')}</textarea>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" id="edit-group-cancel">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
    
    // Bind form events
    this.bindEditFormEvents();
}
```

**Step 3: Handle Form Submission** (45 min)
```javascript
bindEditFormEvents() {
    const form = document.getElementById('edit-group-form');
    const modal = document.getElementById('edit-group-modal');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const data = {
            name: document.getElementById('edit-group-name').value,
            description: document.getElementById('edit-group-description').value
        };
        
        await this.updateGroup(this.currentGroup.id, data);
    });
    
    document.getElementById('edit-group-modal-close').addEventListener('click', () => {
        modal.remove();
    });
    
    document.getElementById('edit-group-cancel').addEventListener('click', () => {
        modal.remove();
    });
}

async updateGroup(groupId, data) {
    try {
        const response = await fetch(`/api/groups/${groupId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to update group');
        }
        
        const updatedGroup = await response.json();
        this.currentGroup = updatedGroup;
        
        // Close modal and refresh
        document.getElementById('edit-group-modal').remove();
        this.renderGroupDetails();
        await this.loadGroups();
        
        this.showSuccess('Group updated successfully');
    } catch (error) {
        console.error('Error updating group:', error);
        this.showError('Failed to update group');
    }
}
```

**Step 4: Add CSS Styling** (30 min)
- Ensure modal styles match existing design
- Add responsive layout
- Test on mobile

**Testing:**
- ✅ Can open edit form
- ✅ Form pre-populates with current data
- ✅ Can save changes
- ✅ Group list updates
- ✅ Group details update
- ✅ Can cancel without saving

**Related Test:** `test_edit_group_multiple_times_all_fields`

---

## 🟡 MEDIUM PRIORITY

### 2. Delete Group Functionality

**Status:** No button or functionality exists  
**Files to Modify:** `src/static/groups.js`, `src/static/groups.html`  
**Estimated Time:** 1-2 hours

#### What's Needed

**Step 1: Add Delete Button** (10 min)
```javascript
// In group details section (around line 56)
<div class="group-actions">
    <button class="btn btn-secondary btn-sm" id="edit-group-btn">
        <i class="fas fa-edit"></i> Edit
    </button>
    <button class="btn btn-danger btn-sm" id="delete-group-btn">
        <i class="fas fa-trash"></i> Delete
    </button>
    <button class="btn btn-success btn-sm" id="create-group-board-btn">
        <i class="fas fa-plus"></i> Create Board
    </button>
</div>
```

**Step 2: Add Event Listener** (5 min)
```javascript
// In bindEvents()
document.getElementById('delete-group-btn').addEventListener('click', () => {
    this.deleteGroup();
});
```

**Step 3: Implement Delete with Confirmation** (45 min)
```javascript
async deleteGroup() {
    if (!this.currentGroup) return;
    
    const groupName = this.currentGroup.name;
    const confirmMessage = `Are you sure you want to delete "${groupName}"?\n\nThis action cannot be undone and will remove all group members and permissions.`;
    
    if (!confirm(confirmMessage)) return;
    
    try {
        const response = await fetch(`/api/groups/${this.currentGroup.id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete group');
        }
        
        // Hide details and refresh list
        document.getElementById('group-details').style.display = 'none';
        this.currentGroup = null;
        await this.loadGroups();
        
        this.showSuccess('Group deleted successfully');
    } catch (error) {
        console.error('Error deleting group:', error);
        this.showError('Failed to delete group');
    }
}
```

**Step 4: Add Permission Check** (15 min)
```javascript
// Only show delete button if user is owner
renderGroupDetails() {
    // ... existing code ...
    
    const deleteBtn = document.getElementById('delete-group-btn');
    if (this.currentGroup.user_role === 'owner') {
        deleteBtn.style.display = 'inline-block';
    } else {
        deleteBtn.style.display = 'none';
    }
}
```

**Testing:**
- ✅ Delete button only visible to owners
- ✅ Confirmation dialog appears
- ✅ Can cancel deletion
- ✅ Group is deleted on confirm
- ✅ Returns to groups list
- ✅ Group removed from list

**Related Test:** `test_delete_group`

---

### 3. Add Column to Board

**Status:** No UI exists  
**Files to Modify:** `src/static/app.js`, `src/static/index.html`  
**Estimated Time:** 2-3 hours

#### What's Needed

**Step 1: Add "Add Column" Button** (15 min)
```html
<!-- In index.html, after columns container -->
<div class="kanban-board">
    <div id="columns-container" class="columns-container">
        <!-- Existing columns -->
    </div>
    <div class="add-column-container">
        <button id="add-column-btn" class="btn btn-secondary add-column-btn">
            <i class="fas fa-plus"></i> Add Column
        </button>
    </div>
</div>
```

**Step 2: Create Inline Column Form** (45 min)
```javascript
// In app.js
showAddColumnForm() {
    const container = document.querySelector('.add-column-container');
    
    container.innerHTML = `
        <div class="add-column-form">
            <input type="text" 
                   id="new-column-name" 
                   placeholder="Column name" 
                   class="form-control"
                   maxlength="50">
            <div class="form-actions">
                <button id="save-column-btn" class="btn btn-primary btn-sm">
                    <i class="fas fa-check"></i> Add
                </button>
                <button id="cancel-column-btn" class="btn btn-secondary btn-sm">
                    <i class="fas fa-times"></i> Cancel
                </button>
            </div>
        </div>
    `;
    
    document.getElementById('new-column-name').focus();
    
    // Bind events
    document.getElementById('save-column-btn').addEventListener('click', () => {
        this.createColumn();
    });
    
    document.getElementById('cancel-column-btn').addEventListener('click', () => {
        this.hideAddColumnForm();
    });
    
    // Enter to save, Escape to cancel
    document.getElementById('new-column-name').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this.createColumn();
        if (e.key === 'Escape') this.hideAddColumnForm();
    });
}

hideAddColumnForm() {
    const container = document.querySelector('.add-column-container');
    container.innerHTML = `
        <button id="add-column-btn" class="btn btn-secondary add-column-btn">
            <i class="fas fa-plus"></i> Add Column
        </button>
    `;
    
    document.getElementById('add-column-btn').addEventListener('click', () => {
        this.showAddColumnForm();
    });
}
```

**Step 3: Implement Create Column API Call** (45 min)
```javascript
async createColumn() {
    const nameInput = document.getElementById('new-column-name');
    const name = nameInput.value.trim();
    
    if (!name) {
        this.showError('Column name is required');
        return;
    }
    
    try {
        const response = await this.apiCall('/columns/', {
            method: 'POST',
            body: JSON.stringify({
                board_id: this.currentBoard.id,
                name: name,
                position: this.columns.length
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to create column');
        }
        
        const column = await response.json();
        
        // Add to columns array and re-render
        this.columns.push(column);
        this.hideAddColumnForm();
        this.renderBoard();
        
        this.showSuccess('Column added successfully');
    } catch (error) {
        console.error('Error creating column:', error);
        this.showError('Failed to create column');
    }
}
```

**Step 4: Add CSS Styling** (30 min)
```css
.add-column-container {
    min-width: 300px;
    padding: 1rem;
}

.add-column-btn {
    width: 100%;
    min-height: 100px;
    border: 2px dashed #ccc;
    background: transparent;
}

.add-column-btn:hover {
    border-color: #007bff;
    background: rgba(0, 123, 255, 0.05);
}

.add-column-form {
    background: white;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.add-column-form input {
    margin-bottom: 0.5rem;
}

.add-column-form .form-actions {
    display: flex;
    gap: 0.5rem;
}
```

**Testing:**
- ✅ Add column button appears
- ✅ Click shows inline form
- ✅ Can enter column name
- ✅ Enter key saves
- ✅ Escape key cancels
- ✅ Column appears in board
- ✅ Can add multiple columns
- ✅ Position is correct

**Related Test:** `test_create_new_column`

---

## 🟢 LOW PRIORITY

### 4. Manage Group Members

**Status:** No UI exists  
**Files to Modify:** `src/static/groups.js`  
**Estimated Time:** 4-6 hours

#### What's Needed

**Step 1: Add "Add Member" Button** (15 min)
```javascript
// In group details section
<div class="group-members">
    <div class="members-header">
        <h4>Members</h4>
        <button class="btn btn-primary btn-sm" id="add-member-btn">
            <i class="fas fa-user-plus"></i> Add Member
        </button>
    </div>
    <div id="members-list" class="members-list"></div>
</div>
```

**Step 2: Create Add Member Modal** (1 hour)
```javascript
showAddMemberForm() {
    // Create modal with email/username input
    // Search for users
    // Select role (member/admin)
    // Add to group
}
```

**Step 3: Implement Member Management** (2 hours)
```javascript
async addMember(userId, role) {
    // POST /api/groups/{id}/members
}

async removeMember(userId) {
    // DELETE /api/groups/{id}/members/{user_id}
}

async updateMemberRole(userId, role) {
    // PUT /api/groups/{id}/members/{user_id}
}
```

**Step 4: Render Members List** (1 hour)
```javascript
renderMembers() {
    // Show member cards with:
    // - Avatar/name
    // - Email
    // - Role badge
    // - Remove button (if owner)
    // - Change role (if owner)
}
```

**Step 5: Add Permissions** (30 min)
- Only owners can add/remove members
- Only owners can change roles
- Can't remove yourself if you're the last owner

**Testing:**
- ✅ Can add members by email
- ✅ Can set member role
- ✅ Members appear in list
- ✅ Can remove members (if owner)
- ✅ Can change member roles (if owner)
- ✅ Permission checks work

**Related Test:** `test_add_member_to_group`

---

## 📊 Implementation Priority

### Recommended Order:

1. **Edit Group** (High Priority, Quick Win)
   - Most visible missing feature
   - Users expect this to work
   - Relatively simple to implement

2. **Delete Group** (Medium Priority, Quick Win)
   - Completes group CRUD operations
   - Simple implementation
   - Important for cleanup

3. **Add Column** (Medium Priority, Medium Effort)
   - Enhances board customization
   - Users may want custom workflows
   - Moderate complexity

4. **Manage Members** (Low Priority, High Effort)
   - Most complex feature
   - Less frequently used
   - Can be deferred

---

## 🧪 Testing Checklist

After implementing each feature, verify:

- [ ] Feature works in UI
- [ ] Related Playwright test passes
- [ ] No console errors
- [ ] Mobile responsive
- [ ] Proper error handling
- [ ] Loading states shown
- [ ] Success/error messages
- [ ] Keyboard shortcuts work
- [ ] Accessibility (ARIA labels)
- [ ] Works across browsers

---

## 📝 Notes

### Why These Features Are Missing

According to project history, the group collaboration system was implemented in phases:
1. ✅ Backend APIs built and tested (100% complete)
2. ✅ Basic UI (create, view) implemented
3. ⏸️ Advanced UI (edit, delete, members) **planned but not completed**

The buttons were added as **placeholders** for future work, but the JavaScript was never wired up.

### Backend API Status

All backend endpoints are **fully functional and tested**:
- ✅ `PUT /api/groups/{id}` - Update group
- ✅ `DELETE /api/groups/{id}` - Delete group
- ✅ `POST /api/columns/` - Create column
- ✅ `POST /api/groups/{id}/members` - Add member
- ✅ `DELETE /api/groups/{id}/members/{user_id}` - Remove member

**No backend work needed** - only frontend implementation!

---

## 🎯 Success Criteria

When all features are complete:
- ✅ Frontend test pass rate: **100%** (61/61)
- ✅ All UI buttons functional
- ✅ Complete group management workflow
- ✅ Full board customization
- ✅ Comprehensive member management

---

## 📚 Related Documentation

- **API Documentation:** See backend API tests for endpoint details
- **Test Files:** 
  - `tests/frontend/test_group_management.py`
  - `tests/frontend/test_board_management.py`
- **Current Implementation:**
  - `src/static/groups.js` - Group management
  - `src/static/app.js` - Board management
  - `src/static/groups.html` - Groups page

---

**Last Updated:** October 9, 2025  
**Maintained By:** Development Team  
**Status:** Ready for implementation
