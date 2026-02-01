# User Stories - Simple Kanban Board

## Epic 1: Core Kanban Functionality

### US-001 (High Priority)
**As a user, I want to create tasks with title and description so I can track work items**
- **Acceptance Criteria:**
  - Task creation form with title (required), description (optional)
  - New tasks appear in "To Do" column by default
  - Form validation prevents empty titles
  - Tasks display title prominently, description on hover/click
  - Tasks automatically timestamped with creation date
  - Task age displayed as "days open" for tracking progress

### US-002 (High Priority)
**As a user, I want to drag tasks between columns (To Do, In Progress, Done) so I can update status visually**
- **Acceptance Criteria:**
  - Drag-and-drop works on desktop browsers
  - Touch gestures work on mobile devices
  - Visual feedback during drag (ghost image, drop zones)
  - Task position updates immediately
  - Changes persist to database

### US-003 (High Priority)
**As a user, I want tasks to persist between sessions so my work isn't lost**
- **Acceptance Criteria:**
  - Tasks saved to PostgreSQL database
  - Board state restored on page reload
  - No data loss during browser crashes
  - Automatic save on any change
  - Creation and modification timestamps preserved

### US-004 (Medium Priority)
**As a user, I want to edit task details so I can update information as work progresses**
- **Acceptance Criteria:**
  - Click task to open edit modal
  - Modify title and description
  - Save/cancel options
  - Changes reflect immediately in UI

### US-005 (Medium Priority)
**As a user, I want to delete tasks so I can remove completed or cancelled items**
- **Acceptance Criteria:**
  - Delete button/option in task menu
  - Confirmation dialog to prevent accidents
  - Task removed from UI and database
  - No way to accidentally delete multiple tasks

## Epic 2: Board Management & Multi-Board Support

### US-014 (High Priority)
**As a user, I want to create and manage multiple boards so I can organize different projects**
- **Acceptance Criteria:**
  - Board creation form with name and description
  - Board selector dropdown in header
  - Edit board details (name/description)
  - Delete boards with confirmation
  - Each board has independent columns and tasks

### US-015 (Medium Priority)
**As a user, I want to see task aging information so I can identify stale work items**
- **Acceptance Criteria:**
  - Tasks display creation date
  - "Days open" calculation shown on task cards
  - Visual indicators for tasks older than configurable thresholds
  - Sorting options by age or creation date

## Epic 3: Self-Hosting & Control

### US-006 (High Priority)
**As a system admin, I want single-container deployment so I can run it anywhere without dependencies**
- **Acceptance Criteria:**
  - Single `docker run` command starts the application
  - PostgreSQL database included in deployment
  - Runs on port 8000 by default
  - Data persists in mounted volume

### US-007 (High Priority)
**As a developer, I want to modify the UI/workflow so I can customize it for my team's needs**
- **Acceptance Criteria:**
  - Clean, well-documented code structure
  - Separate components for easy modification
  - CSS variables for easy theming
  - Clear API for adding new columns/features

### US-008 (Medium Priority)
**As a user, I want to export/import board data so I can backup and migrate between instances**
- **Acceptance Criteria:**
  - Export board as JSON file
  - Import JSON to restore board state
  - Validation of imported data
  - Clear error messages for invalid imports

### US-009 (Low Priority)
**As a system admin, I want configuration via environment variables so I can customize behavior without code changes**
- **Acceptance Criteria:**
  - Database path configurable
  - Port number configurable
  - Basic theming options via env vars
  - Documentation of all available options

## Epic 3: Performance & Security

### US-010 (High Priority)
**As a user, I want fast page loads and responsive interactions so the tool doesn't slow me down**
- **Acceptance Criteria:**
  - Initial page load under 2 seconds
  - Drag operations feel smooth (60fps)
  - API responses under 100ms
  - Minimal JavaScript bundle size

### US-011 (Medium Priority)
**As a system admin, I want the container to run as non-root so it follows security best practices**
- **Acceptance Criteria:**
  - Container runs as user 1000:1000 ✅
  - No privileged operations required ✅
  - Read-only root filesystem where possible ✅
  - Security context configured in Helm chart ✅
  - Database passwords use secure secrets instead of hardcoded values ✅
  - Environment-specific secret management patterns ✅

### US-013 (Medium Priority)
**As a system admin, I want comprehensive observability so I can monitor application health and performance**
- **Acceptance Criteria:**
  - OpenTelemetry tracing exports to Prometheus Gateway
  - Local `/metrics` endpoint for Prometheus scraping
  - Health checks include dependency status
  - Structured logging with correlation IDs
  - Business metrics (task creation/completion rates)
  - Performance metrics (response times, error rates)

### US-012 (Low Priority)
**As a user, I want keyboard shortcuts so I can work efficiently**
- **Acceptance Criteria:**
  - 'N' to create new task
  - Arrow keys to move between tasks
  - Enter to edit selected task
  - Delete key to remove selected task
  - Escape to cancel operations

## Story Prioritization

**Phase 1 (MVP):** US-001, US-002, US-003, US-006, US-010, US-011, US-013, US-014
**Phase 2 (Enhancement):** US-004, US-005, US-007, US-008, US-015
**Phase 3 (Polish):** US-009, US-012

## Implementation Status

**✅ Completed:**
- US-001: Task creation with timestamps ✅
- US-002: Drag-and-drop functionality ✅
- US-003: PostgreSQL persistence ✅
- US-004: Task editing ✅
- US-005: Task deletion ✅
- US-006: Container deployment ✅
- US-011: Non-root security with secure password management ✅
- US-014: Multi-board management ✅

**✅ Completed (MVP):**
- US-001: Basic kanban functionality
- US-002: Task management
- US-003: Drag-and-drop operations
- US-006: Board management
- US-010: Data persistence
- US-011: Self-hosted deployment
- US-013: Task timestamps
- US-014: Board CRUD operations
- US-015: Task aging display with color indicators

**📋 Planned:**
- US-007: UI customization framework
- US-008: Export/import functionality
- US-010: Performance optimization
- US-013: Observability implementation
- US-009: Environment configuration
- US-012: Keyboard shortcuts

## Epic 4: Multi-User Authentication & Authorization

### US-016 (High Priority)
**As a user, I want to sign in with my Google account so I can securely access my boards**
- **Acceptance Criteria:**
  - Google OIDC integration for authentication
  - User profile creation from Google account data
  - Secure session management with JWT tokens
  - Automatic user profile updates from Google
  - Logout functionality that clears all sessions

### US-017 (High Priority)
**As a board owner, I want to control who can access my boards so I can manage collaboration**
- **Acceptance Criteria:**
  - Board ownership assigned to creator
  - Invite users by email address
  - Assign roles: Owner, Editor, Viewer
  - Remove users from board access
  - Transfer board ownership

### US-018 (Medium Priority)
**As a board member, I want different permission levels so I can contribute appropriately**
- **Acceptance Criteria:**
  - Viewers can only read board contents
  - Editors can create/edit/delete tasks and move them
  - Owners can modify board settings and manage members
  - UI reflects available actions based on permissions
  - Clear indication of current user's role

### US-019 (Medium Priority)
**As a user, I want to see only my accessible boards so I can focus on relevant work**
- **Acceptance Criteria:**
  - Dashboard shows boards where user has access
  - Filter boards by role (owned, shared with me)
  - Search boards by name or description
  - Recent boards list for quick access
  - Board access indicators (owner/editor/viewer)

### US-020 (Low Priority)
**As a system admin, I want to manage users and system settings so I can maintain the platform**
- **Acceptance Criteria:**
  - Admin interface for user management
  - Deactivate/reactivate user accounts
  - View system usage statistics
  - Manage global system settings
  - Audit trail for administrative actions

## Updated Story Prioritization

**Phase 1 (MVP - Current):** US-001, US-002, US-003, US-006, US-010, US-011, US-013, US-014, US-015
**Phase 2 (Multi-User):** US-016, US-017, US-018, US-019
**Phase 3 (Enhancement):** US-004, US-005, US-007, US-008, US-020
**Phase 4 (Polish):** US-009, US-012
