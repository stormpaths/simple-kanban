# Testing Plan for UI Improvements

**Branch:** `feature/group-ui-and-docker-fixes`  
**Date:** October 10, 2025  
**Features to Test:** Edit Group, Delete Group, Add Column

---

## 🎯 **Testing Objectives**

1. Verify all new UI features work correctly
2. Ensure no regressions in existing functionality
3. Validate backend API integration
4. Check error handling and edge cases
5. Confirm user experience is smooth

---

## 🧪 **Manual Testing Checklist**

### **1. Edit Group Feature** ✅

**Prerequisites:**
- User must be logged in
- User must have at least one group created
- User must be the owner of the group

**Test Cases:**

- [ ] **TC-1.1:** Click "Edit" button on group details
  - **Expected:** Edit form appears with current name and description pre-filled
  
- [ ] **TC-1.2:** Modify group name and save
  - **Expected:** Group name updates, success message shown, list refreshes
  
- [ ] **TC-1.3:** Modify group description and save
  - **Expected:** Description updates, success message shown
  
- [ ] **TC-1.4:** Clear description (make it empty) and save
  - **Expected:** Description becomes empty, updates successfully
  
- [ ] **TC-1.5:** Click "Cancel" button
  - **Expected:** Form closes, returns to group details, no changes saved
  
- [ ] **TC-1.6:** Try to save with empty name
  - **Expected:** Form validation prevents submission (HTML5 required)
  
- [ ] **TC-1.7:** Try to save with very long name (>255 chars)
  - **Expected:** Form validation prevents submission (maxlength)
  
- [ ] **TC-1.8:** Edit group that has members
  - **Expected:** Updates successfully, members remain
  
- [ ] **TC-1.9:** Edit group that has boards
  - **Expected:** Updates successfully, boards remain linked

**XSS Testing:**
- [ ] **TC-1.10:** Try to save name with `<script>alert('XSS')</script>`
  - **Expected:** Escaped properly, no script execution

---

### **2. Delete Group Feature** ✅

**Prerequisites:**
- User must be logged in
- User must have at least one group created
- User must be the owner of the group

**Test Cases:**

- [ ] **TC-2.1:** Click "Delete" button on group details
  - **Expected:** Confirmation dialog appears with warnings
  
- [ ] **TC-2.2:** Read confirmation message
  - **Expected:** Message explains:
    - Removes all members
    - Unlinks group boards (boards remain)
    - Cannot be undone
  
- [ ] **TC-2.3:** Click "Cancel" in confirmation dialog
  - **Expected:** Dialog closes, group not deleted
  
- [ ] **TC-2.4:** Click "OK" in confirmation dialog
  - **Expected:** Group deletes, success message shown, list refreshes
  
- [ ] **TC-2.5:** Delete group with no members
  - **Expected:** Deletes successfully
  
- [ ] **TC-2.6:** Delete group with multiple members
  - **Expected:** Deletes successfully, members removed
  
- [ ] **TC-2.7:** Delete group with linked boards
  - **Expected:** Deletes successfully, boards become personal
  
- [ ] **TC-2.8:** After deleting group, check boards still exist
  - **Expected:** Boards remain accessible, no longer linked to group
  
- [ ] **TC-2.9:** Try to delete last group
  - **Expected:** Deletes successfully, returns to empty group list

---

### **3. Add Column Feature** ✅

**Prerequisites:**
- User must be logged in
- User must have at least one board created
- User must have selected a board

**Test Cases:**

- [ ] **TC-3.1:** Click "Add Column" button on board header
  - **Expected:** Column modal appears with empty form
  
- [ ] **TC-3.2:** Enter column name "In Progress" and submit
  - **Expected:** Column creates at end, board refreshes, success message shown
  
- [ ] **TC-3.3:** Enter column name and position "0" (leftmost)
  - **Expected:** Column creates at position 0 (leftmost)
  
- [ ] **TC-3.4:** Enter column name and position "1" (second)
  - **Expected:** Column creates at position 1
  
- [ ] **TC-3.5:** Enter column name without position
  - **Expected:** Column creates at end (default behavior)
  
- [ ] **TC-3.6:** Click "Cancel" button
  - **Expected:** Modal closes, no column created
  
- [ ] **TC-3.7:** Click backdrop (outside modal)
  - **Expected:** Modal closes, no column created
  
- [ ] **TC-3.8:** Press ESC key
  - **Expected:** Modal closes, no column created
  
- [ ] **TC-3.9:** Try to submit with empty name
  - **Expected:** Form validation prevents submission (HTML5 required)
  
- [ ] **TC-3.10:** Enter very long column name (>255 chars)
  - **Expected:** Input limited by maxlength or backend validation
  
- [ ] **TC-3.11:** Enter negative position
  - **Expected:** Form validation prevents (min="0")
  
- [ ] **TC-3.12:** Add column to board with existing tasks
  - **Expected:** Column creates, existing tasks remain in their columns
  
- [ ] **TC-3.13:** Add multiple columns in sequence
  - **Expected:** Each column creates successfully

**Edge Cases:**
- [ ] **TC-3.14:** Try to add column without selecting a board
  - **Expected:** Error message "Please select a board first"

---

## 🤖 **Automated Testing**

### **Frontend E2E Tests to Update:**

**File:** `tests/frontend/test_group_management.py`

**New Tests Needed:**

```python
def test_edit_group_success(page, auth_context):
    """Test editing a group name and description"""
    # Create a group
    # Click edit button
    # Modify name and description
    # Submit form
    # Verify group updated
    pass

def test_edit_group_cancel(page, auth_context):
    """Test canceling group edit"""
    # Create a group
    # Click edit button
    # Modify fields
    # Click cancel
    # Verify no changes saved
    pass

def test_delete_group_with_confirmation(page, auth_context):
    """Test deleting a group with confirmation"""
    # Create a group
    # Click delete button
    # Verify confirmation dialog
    # Confirm deletion
    # Verify group deleted
    pass

def test_delete_group_cancel(page, auth_context):
    """Test canceling group deletion"""
    # Create a group
    # Click delete button
    # Cancel in dialog
    # Verify group still exists
    pass
```

**File:** `tests/frontend/test_board_operations.py` (new or existing)

**New Tests Needed:**

```python
def test_add_column_success(page, auth_context, board_with_columns):
    """Test adding a new column to a board"""
    # Open board
    # Click "Add Column" button
    # Enter column name
    # Submit form
    # Verify column appears
    pass

def test_add_column_with_position(page, auth_context, board_with_columns):
    """Test adding a column at specific position"""
    # Open board
    # Click "Add Column"
    # Enter name and position 0
    # Submit
    # Verify column at leftmost position
    pass

def test_add_column_cancel(page, auth_context, board_with_columns):
    """Test canceling column creation"""
    # Open board
    # Click "Add Column"
    # Enter name
    # Click cancel
    # Verify column not created
    pass
```

---

## 🔄 **Regression Testing**

### **Existing Features to Verify:**

- [ ] **Board Creation** - Still works
- [ ] **Task Creation** - Still works
- [ ] **Task Movement** - Still works (drag and drop)
- [ ] **Group Creation** - Still works
- [ ] **Group Board Creation** - Still works
- [ ] **User Authentication** - Still works
- [ ] **API Key Management** - Still works

---

## 🚀 **Deployment Testing Sequence**

### **Step 1: Local Testing**
```bash
# Start local dev environment
make dev

# Wait for deployment
kubectl get pods -n apps-dev

# Run manual tests
# Open https://kanban.stormpath.dev
```

### **Step 2: Automated Tests**
```bash
# Run backend tests
make test-backend

# Run frontend tests
make test-frontend

# Run all tests
make test
```

### **Step 3: Dev Environment Testing**
```bash
# Deploy to dev
skaffold run -p dev

# Wait for deployment
kubectl rollout status deployment/simple-kanban-dev -n apps-dev

# Run tests against dev
BASE_URL=https://kanban.stormpath.dev make test
```

### **Step 4: Production Deployment** (After all tests pass)
```bash
# Merge to main branch
git checkout kanban-main1
git merge feature/group-ui-and-docker-fixes

# Deploy to production
skaffold run -p prod

# Run tests against production
make test-production
```

---

## 📊 **Expected Test Results**

### **Before Changes:**
- Backend: 10/10 (100%)
- Frontend: 47/51 (92%)
- Overall: 57/61 (93%)
- Skipped: 4 tests

### **After Changes:**
- Backend: 10/10 (100%) - No change
- Frontend: 51/51 (100%) - +4 tests passing
- Overall: 61/61 (100%) - Perfect!
- Skipped: 0 tests

### **Test Coverage Improvement:**
- **+4 tests** (edit group, delete group, add column, manage members)
- **+7% coverage** (93% → 100%)
- **0 skipped tests** (4 → 0)

---

## ⚠️ **Known Issues / Limitations**

### **Current Implementation:**

1. **Manage Members UI** - Not yet implemented (in progress)
   - This is the 4th feature from evaluation
   - Will add another test when complete

2. **Column Reordering** - Not implemented
   - Can set position on creation
   - Cannot drag to reorder (future feature)

3. **Column Editing** - Not implemented
   - Can create columns
   - Cannot edit name after creation (future feature)

4. **Column Deletion** - Not implemented
   - Can create columns
   - Cannot delete columns (future feature)

---

## ✅ **Success Criteria**

### **Feature Acceptance:**
- ✅ All manual test cases pass
- ✅ No regressions in existing features
- ✅ Automated tests updated and passing
- ✅ Error handling works correctly
- ✅ User experience is smooth
- ✅ Backend APIs integrate properly

### **Deployment Acceptance:**
- ✅ Dev deployment successful
- ✅ All tests pass in dev
- ✅ Manual QA in dev successful
- ✅ Production deployment successful
- ✅ All tests pass in production

---

## 🐛 **Bug Tracking**

### **Issues Found:**
(To be filled during testing)

| ID | Feature | Issue | Severity | Status |
|----|---------|-------|----------|--------|
| - | - | - | - | - |

---

## 📝 **Testing Notes**

### **Testing Environment:**
- **Dev URL:** https://kanban.stormpath.dev
- **Prod URL:** https://kanban.stormpath.net
- **Test User:** (Create fresh test user for each session)

### **Test Data:**
- Create fresh groups for testing
- Create fresh boards for testing
- Don't use production data for destructive tests

### **Browser Testing:**
- Primary: Chrome/Chromium (Playwright default)
- Secondary: Firefox (if issues found)
- Mobile: Responsive design (if time permits)

---

**Status:** 🔄 Ready for Testing  
**Next Step:** Deploy to dev and run manual tests  
**Expected Duration:** 30-45 minutes for complete testing
