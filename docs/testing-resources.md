# Testing Resources Summary

**Last Updated**: October 4, 2025  
**Status**: Complete automated testing infrastructure with comprehensive authentication testing

## Overview

The Simple Kanban Board now features a comprehensive automated testing system that runs after every deployment, ensuring quality and reliability. Tests cover authentication, group collaboration, API functionality, admin features, and security validation.

## Automated Testing Integration

### Skaffold Post-Deploy Hooks
Every `skaffold run` automatically executes our test battery:
- **Development**: Comprehensive tests with soft-fail mode (reports issues but allows deployment)
- **Production**: Full validation with hard-fail mode (blocks deployment on test failure)
- **Feature**: Quick smoke tests for rapid iteration

### Test Execution Modes
```bash
# Automatic (via Skaffold)
skaffold run -p dev    # Runs full test battery automatically

# Manual execution
./scripts/test-all.sh --quick    # ~15 seconds, smoke tests
./scripts/test-all.sh --full     # ~45 seconds, comprehensive
./scripts/test-all.sh --verbose  # Detailed debugging output
```

## Test Categories

### 1. Health & Infrastructure Tests
- Application availability and responsiveness
- Database connectivity
- Service health endpoints

### 2. Authentication & Authorization Tests (**COMPREHENSIVE**)
- **Complete JWT Testing**: Login, token validation, protected endpoint access
- **User Registration Testing**: Signup workflow, validation, duplicate prevention
- **API Key Authentication**: Scoped permissions, management endpoints
- **Cross-Authentication**: JWT ↔ API key compatibility and consistency
- **Security Controls**: Invalid credential rejection, access control validation
- **Dual Authentication**: All endpoints tested with both JWT and API key methods

### 3. Group Collaboration Tests (**NEW**)
- Group creation, update, and deletion
- Member management (add/remove users)
- Group-owned board creation and access
- Access control validation
- Cascade deletion testing

### 4. API Functionality Tests
- Complete CRUD operations for boards, columns, tasks
- Board management and persistence
- Task movement and drag-drop functionality
- Comment system validation

### 5. Admin Interface Tests
- Administrative dashboard access
- User management functionality
- System statistics and metrics
- API key administration

### 6. Security Validation Tests
- Rate limiting enforcement
- CSRF protection validation
- Security headers verification
- Input validation and sanitization

## Kubernetes Secrets for Testing

### Primary Test API Key

**Secret Name**: `simple-kanban-test-api-key`  
**Namespace**: `apps-dev`  
**Purpose**: Main API key for automated testing

```bash
# Access the secret
kubectl get secret simple-kanban-test-api-key -n apps-dev -o yaml

# Get API key value
kubectl get secret simple-kanban-test-api-key -n apps-dev -o jsonpath='{.data.api-key}' | base64 -d
```

**Contents**:
- `api-key`: `sk_***REDACTED***` (retrieved from Kubernetes secret)
- `key-name`: `dev`
- `user-id`: `1` (admin user)
- `scopes`: `read,write,docs,admin`

## Test Scripts

### 1. Comprehensive Test Battery
**File**: `scripts/test-all.sh`  
**Purpose**: Complete application validation suite

```bash
./scripts/test-all.sh --quick    # Quick smoke tests (~35s)
./scripts/test-all.sh --full     # Full validation (~45s)
./scripts/test-all.sh --verbose  # Detailed debugging output
```

**Test Coverage**:
- ✅ Health checks and infrastructure
- ✅ **Comprehensive Authentication System** (JWT + API keys + registration)
- ✅ API endpoints (boards, tasks, columns) with dual authentication
- ✅ Group collaboration system
- ✅ Admin interface and statistics
- ✅ Security validation and access control

### 1.5. Authentication Test Suite (**NEW**)
**File**: `scripts/test-auth-comprehensive.sh`  
**Purpose**: Complete authentication system validation

```bash
./scripts/test-auth-comprehensive.sh           # Full authentication testing
./scripts/test-auth-comprehensive.sh --quick   # Quick authentication validation
```

**Test Coverage**:
- ✅ JWT authentication workflow (login, token validation, protected access)
- ✅ User registration and signup validation
- ✅ Cross-authentication validation (JWT ↔ API key compatibility)
- ✅ Security controls (invalid auth rejection, access control)
- ✅ API coverage validation (all endpoints tested with both auth methods)

### 2. Group Collaboration Testing (**NEW**)
**File**: `scripts/test-groups.sh`  
**Purpose**: Complete group management validation

```bash
./scripts/test-groups.sh
```

**Tests**:
- ✅ Group creation, update, deletion
- ✅ Member management (add/remove users)
- ✅ Group-owned board creation and access
- ✅ Access control and permissions
- ✅ Cascade deletion validation

### 3. API Key Testing Suite
**File**: `scripts/test-api-key.sh`  
**Purpose**: Comprehensive API key authentication testing

```bash
./scripts/test-api-key.sh
```

**Tests**:
- ✅ Board API endpoints
- ✅ API key management endpoints  
- ✅ Secured documentation access
- ✅ Authentication validation
- ✅ Invalid key rejection

### 4. Post-Deploy Validation
**File**: `scripts/post-deploy-test.sh`  
**Purpose**: Automated testing after Skaffold deployments

```bash
./scripts/post-deploy-test.sh dev full soft    # Development mode
./scripts/post-deploy-test.sh prod full hard   # Production mode
```

**Features**:
- ✅ Waits for deployment readiness
- ✅ Environment-specific test modes
- ✅ Soft/hard failure modes
- ✅ Detailed logging and reporting

### 5. Test User Creation
**File**: `scripts/create-test-user.sh`  
**Purpose**: Create new test users with API keys

```bash
./scripts/create-test-user.sh
```

**Creates**:
- New user account
- JWT token for the user
- API key with limited scopes
- Kubernetes secret with all credentials

## Test User Accounts

### Admin Test User (User ID 1)
- **Username**: Admin user (first user)
- **API Key**: Stored in `simple-kanban-test-api-key` secret
- **Scopes**: Full admin access (`read,write,docs,admin`)
- **Purpose**: Testing admin-level API operations

### Generated Test Users
Created via `create-test-user.sh` script:
- **Username Pattern**: `testuser_<timestamp>`
- **Email Pattern**: `test_<timestamp>@example.com`
- **API Key Scopes**: Limited (`read,write`)
- **Secret Pattern**: `simple-kanban-test-user-<user_id>`

## API Endpoints for Testing

### Public Endpoints (No Authentication)
- `GET /health` - Health check
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login

### Protected Endpoints (Require API Key)
- `GET /api/boards/` - List boards
- `GET /api/boards/{id}` - Get board details
- `POST /api/boards/` - Create board
- `PUT /api/boards/{id}` - Update board
- `DELETE /api/boards/{id}` - Delete board

### API Key Management
- `GET /api/api-keys/` - List user's API keys
- `POST /api/api-keys/` - Create new API key
- `GET /api/api-keys/{id}` - Get API key details
- `PUT /api/api-keys/{id}` - Update API key
- `DELETE /api/api-keys/{id}` - Delete API key
- `GET /api/api-keys/stats/usage` - Usage statistics

### Secured Documentation
- `GET /docs` - Swagger UI (requires `docs` scope)
- `GET /redoc` - ReDoc documentation (requires `docs` scope)
- `GET /openapi.json` - OpenAPI schema (requires `docs` scope)

## Testing Scenarios

### 1. Basic Authentication
```bash
API_KEY=$(kubectl get secret simple-kanban-test-api-key -n apps-dev -o jsonpath='{.data.api-key}' | base64 -d)
curl -H "Authorization: Bearer $API_KEY" https://kanban.stormpath.dev/api/boards/
```

### 2. Scope Validation
```bash
# Test admin scope (should work with main test key)
curl -H "Authorization: Bearer $API_KEY" https://kanban.stormpath.dev/docs

# Test with limited scope key (create via create-test-user.sh)
curl -H "Authorization: Bearer $LIMITED_KEY" https://kanban.stormpath.dev/docs  # Should fail
```

### 3. Invalid Authentication
```bash
# No authentication
curl https://kanban.stormpath.dev/api/boards/  # Should return 401

# Invalid key
curl -H "Authorization: Bearer sk_invalid" https://kanban.stormpath.dev/api/boards/  # Should return 401
```

## Cleanup Commands

### Remove Test Secrets
```bash
# Remove main test secret
kubectl delete secret simple-kanban-test-api-key -n apps-dev

# Remove generated test user secrets
kubectl get secrets -n apps-dev | grep simple-kanban-test-user | awk '{print $1}' | xargs kubectl delete secret -n apps-dev
```

### Remove Test Users (via API)
```bash
# List users to find test users
curl -H "Authorization: Bearer $ADMIN_API_KEY" https://kanban.stormpath.dev/api/admin/users

# Note: User deletion would need to be implemented in admin API
```

## Integration with CI/CD

### GitHub Actions Example
```yaml
name: API Key Tests
on: [push, pull_request]
jobs:
  test-api-keys:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup kubectl
        uses: azure/setup-kubectl@v1
      - name: Run API Key Tests
        run: ./scripts/test-api-key.sh
```

### Kubernetes Job Example
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: api-key-test
  namespace: apps-dev
spec:
  template:
    spec:
      containers:
      - name: test
        image: curlimages/curl
        command: ["/bin/sh"]
        args: ["-c", "curl -H 'Authorization: Bearer $(cat /secrets/api-key)' https://kanban.stormpath.dev/api/boards/"]
        volumeMounts:
        - name: api-key
          mountPath: /secrets
      volumes:
      - name: api-key
        secret:
          secretName: simple-kanban-test-api-key
      restartPolicy: Never
```

## Security Notes

### Production Considerations
- 🔒 Test secrets should never be used in production
- 🔒 API keys should have minimal required scopes
- 🔒 Test users should be cleaned up regularly
- 🔒 Monitor API key usage in production

### Secret Management
- All test credentials are stored in Kubernetes secrets
- Secrets are namespace-scoped (`apps-dev`)
- Use RBAC to control access to test secrets
- Rotate test API keys periodically

## Troubleshooting

### Common Issues
1. **Secret not found**: Check namespace and secret name
2. **API key expired**: Create new key or extend expiration
3. **Permission denied**: Verify scopes match endpoint requirements
4. **Network issues**: Check application health and connectivity

### Debug Commands
```bash
# Check application health
curl https://kanban.stormpath.dev/health

# View application logs
kubectl logs -f deployment/simple-kanban-dev -n apps-dev

# List all test secrets
kubectl get secrets -n apps-dev | grep simple-kanban-test

# Decode secret values
kubectl get secret <secret-name> -n apps-dev -o jsonpath='{.data}' | jq -r 'to_entries[] | "\(.key): \(.value | @base64d)"'
```
