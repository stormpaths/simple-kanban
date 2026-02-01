# Database Schema Documentation

## Overview

The Simple Kanban Board uses a PostgreSQL database with four main tables supporting the kanban board functionality and user authentication.

## Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│    Users    │       │   Boards    │       │   Columns   │       │    Tasks    │
├─────────────┤       ├─────────────┤       ├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │       │ id (PK)     │       │ id (PK)     │
│ username    │       │ name        │       │ name        │       │ title       │
│ email       │       │ description │       │ position    │       │ description │
│ hashed_pwd  │       │ created_at  │       │ board_id FK │◄──────┤ position    │
│ is_active   │       │ updated_at  │       │ created_at  │       │ column_id FK│
│ is_admin    │       └─────────────┘       │ updated_at  │       │ created_at  │
│ created_at  │                             └─────────────┘       │ updated_at  │
│ updated_at  │                                                   └─────────────┘
└─────────────┘
```

## Table Definitions

### Users Table
Stores user authentication and profile information.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing user ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Unique username for login |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE | Account active status |
| is_admin | BOOLEAN | NOT NULL, DEFAULT FALSE | Admin privileges flag |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Account creation time |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update time |

**Indexes:**
- `ix_users_username` (UNIQUE)
- `ix_users_email` (UNIQUE)

### Boards Table
Stores kanban board information (supports future multi-board functionality).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing board ID |
| name | VARCHAR(255) | NOT NULL | Board display name |
| description | TEXT | NULLABLE | Optional board description |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Board creation time |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update time |

### Columns Table
Stores kanban board columns (To Do, In Progress, Done).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing column ID |
| name | VARCHAR(100) | NOT NULL | Column display name |
| position | INTEGER | NOT NULL, DEFAULT 0 | Column order position |
| board_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to boards.id |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Column creation time |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update time |

**Foreign Keys:**
- `board_id` → `boards.id` (CASCADE DELETE)

**Indexes:**
- `ix_columns_board_id`
- `ix_columns_position`

### Tasks Table
Stores individual kanban tasks.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-incrementing task ID |
| title | VARCHAR(255) | NOT NULL | Task title/summary |
| description | TEXT | NULLABLE | Optional task description |
| position | INTEGER | NOT NULL, DEFAULT 0 | Task order within column |
| column_id | INTEGER | FOREIGN KEY, NOT NULL | Reference to columns.id |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Task creation time |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last update time |

**Foreign Keys:**
- `column_id` → `columns.id` (CASCADE DELETE)

**Indexes:**
- `ix_tasks_column_id`
- `ix_tasks_position`

## Key Design Decisions

### Timestamps
All tables include `created_at` and `updated_at` timestamps with timezone support for audit trails and synchronization.

### Cascade Deletes
- Deleting a board removes all its columns and tasks
- Deleting a column removes all its tasks
- This maintains referential integrity

### Position Fields
Both columns and tasks have position fields to support drag-and-drop reordering functionality.

### Future Extensibility
- Board table supports future multi-board functionality
- User table includes admin flags for future role-based access
- Schema can be extended without breaking existing functionality

## Migration Strategy

The initial schema is created via Alembic migration `001_initial_schema.py`. Future schema changes will use versioned migrations to ensure safe database updates.

## Performance Considerations

### Indexes
- Foreign key columns are indexed for join performance
- Position columns are indexed for ordering queries
- Unique constraints on username/email for fast authentication lookups

### Query Patterns
The schema is optimized for common kanban operations:
- Loading all tasks for a board (via column relationships)
- Reordering tasks within columns
- User authentication lookups
- Audit trail queries via timestamps
