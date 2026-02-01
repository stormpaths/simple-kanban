# Authentication & Authorization Design - Simple Kanban Board

## Overview
Design for multi-user support with Google OIDC authentication and role-based access control (RBAC) for board ownership and collaboration.

## Authentication Strategy

### Google OIDC Integration
- **Primary Authentication**: Google OAuth 2.0 / OpenID Connect
- **Local User Profiles**: Link Google accounts to internal user records
- **Session Management**: JWT tokens with refresh capability
- **Fallback**: Optional local authentication for development/testing

### User Profile Structure
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "google_id": "google_oauth_id",
  "avatar_url": "https://...",
  "created_at": "timestamp",
  "last_login": "timestamp",
  "is_active": true,
  "preferences": {
    "theme": "light|dark",
    "notifications": true
  }
}
```

## Authorization Model (RBAC)

### Roles
1. **Board Owner**: Full control over board and its contents
2. **Board Editor**: Can create/edit/delete tasks and columns
3. **Board Viewer**: Read-only access to board contents
4. **System Admin**: Manage users and system settings

### Permissions Matrix
| Action | Owner | Editor | Viewer | Admin |
|--------|-------|--------|--------|-------|
| View Board | ✅ | ✅ | ✅ | ✅ |
| Create Tasks | ✅ | ✅ | ❌ | ✅ |
| Edit Tasks | ✅ | ✅ | ❌ | ✅ |
| Delete Tasks | ✅ | ✅ | ❌ | ✅ |
| Move Tasks | ✅ | ✅ | ❌ | ✅ |
| Edit Board | ✅ | ❌ | ❌ | ✅ |
| Delete Board | ✅ | ❌ | ❌ | ✅ |
| Manage Members | ✅ | ❌ | ❌ | ✅ |
| Export Board | ✅ | ✅ | ✅ | ✅ |

### Board Membership
```json
{
  "board_id": "uuid",
  "user_id": "uuid", 
  "role": "owner|editor|viewer",
  "invited_by": "uuid",
  "invited_at": "timestamp",
  "accepted_at": "timestamp"
}
```

## Database Schema Extensions

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    preferences JSONB DEFAULT '{}'
);
```

### Board Memberships Table
```sql
CREATE TABLE board_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID REFERENCES boards(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
    invited_by UUID REFERENCES users(id),
    invited_at TIMESTAMP DEFAULT NOW(),
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(board_id, user_id)
);
```

### Sessions Table
```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP DEFAULT NOW(),
    user_agent TEXT,
    ip_address INET
);
```

## API Security

### Authentication Middleware
- JWT token validation on protected endpoints
- Google OIDC token verification
- Session management and refresh
- Rate limiting per user

### Authorization Decorators
```python
@require_auth
@require_board_access(role="editor")
async def update_task(board_id: str, task_id: str, user: User):
    # Implementation
```

### Protected Endpoints
- All board operations require authentication
- Board access validated per request
- User context injected into all handlers
- Audit logging for sensitive operations

## Implementation Phases

### Phase 1: User Management
- User registration/profile creation
- Google OIDC integration
- Basic session management
- User preferences

### Phase 2: Board Ownership
- Board-user relationship
- Owner-only operations
- Board creation permissions
- User dashboard

### Phase 3: Collaboration
- Board sharing/invitations
- Role-based permissions
- Member management UI
- Activity notifications

### Phase 4: Advanced Features
- Team/organization support
- Advanced permissions
- Audit trails
- Admin interface

## Security Considerations

### Data Protection
- Encrypt sensitive user data
- Secure session storage
- HTTPS enforcement
- CSRF protection

### Access Control
- Principle of least privilege
- Regular permission audits
- Secure default permissions
- Permission inheritance rules

### Privacy
- GDPR compliance considerations
- User data export/deletion
- Consent management
- Data retention policies

## Configuration

### Environment Variables
```bash
# Google OIDC
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback

# JWT Configuration
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Session Configuration
SESSION_TIMEOUT_HOURS=168  # 1 week
REFRESH_TOKEN_DAYS=30

# Security
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
RATE_LIMIT_PER_MINUTE=60
```

## Migration Strategy

### Backward Compatibility
- Existing boards become "public" initially
- Migration script to assign ownership
- Graceful degradation for unauthenticated users
- Feature flags for gradual rollout

### Data Migration
1. Create user tables
2. Add user_id to boards table
3. Create default admin user
4. Assign existing boards to admin
5. Enable authentication requirements
