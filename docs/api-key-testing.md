# API Key Testing Documentation

## Overview

This document describes the API key testing setup for the Simple Kanban Board application.

## Test API Key Configuration

### Kubernetes Secret

The test API key is stored as a Kubernetes secret for secure access during testing:

```bash
# Secret Details
Namespace: apps-dev
Secret Name: simple-kanban-test-api-key
```

### Secret Contents

| Key | Value | Description |
|-----|-------|-------------|
| `api-key` | `sk_***REDACTED***` | The actual API key for testing (stored in Kubernetes secret) |
| `key-name` | `dev` | Human-readable name of the key |
| `user-id` | `1` | User ID that owns this API key |
| `scopes` | `read,write,docs,admin` | Comma-separated list of scopes |

### API Key Properties

- **Owner**: User ID 1 (admin user)
- **Scopes**: `read`, `write`, `docs`, `admin`
- **Status**: Active
- **Expires**: 2025-10-26
- **Created**: 2025-09-26

## Testing Scripts

### Automated Test Suite

Run the comprehensive API key test suite:

```bash
./scripts/test-api-key.sh
```

This script tests:
- ✅ Board listing and retrieval
- ✅ API key management endpoints
- ✅ Usage statistics
- ✅ Secured documentation access
- ✅ Authentication validation
- ✅ Invalid key rejection

### Manual Testing

#### Retrieve API Key from Secret

```bash
# Get the API key
API_KEY=$(kubectl get secret simple-kanban-test-api-key -n apps-dev -o jsonpath='{.data.api-key}' | base64 -d)

# Use in curl commands
curl -H "Authorization: Bearer $API_KEY" https://kanban.stormpath.dev/api/boards/
```

#### Test Individual Endpoints

```bash
# List boards
curl -H "Authorization: Bearer $API_KEY" \
     https://kanban.stormpath.dev/api/boards/

# Get board details
curl -H "Authorization: Bearer $API_KEY" \
     https://kanban.stormpath.dev/api/boards/1

# List API keys
curl -H "Authorization: Bearer $API_KEY" \
     https://kanban.stormpath.dev/api/api-keys/

# Access documentation
curl -H "Authorization: Bearer $API_KEY" \
     https://kanban.stormpath.dev/docs
```

## Test User Information

The API key is associated with User ID 1, which has the following properties:

- **Username**: Admin user (first user in system)
- **Permissions**: Full admin access
- **Boards**: Can access all boards owned by User ID 1
- **API Keys**: Can manage API keys for User ID 1

## Security Testing

### Valid Authentication Tests

- ✅ API key format validation (`sk_` prefix)
- ✅ Key hash lookup in database
- ✅ Active status verification
- ✅ Expiration date checking
- ✅ Scope validation per endpoint
- ✅ User account status verification

### Invalid Authentication Tests

- ✅ Missing Authorization header → 401
- ✅ Invalid API key format → 401
- ✅ Non-existent API key → 401
- ✅ Expired API key → 401
- ✅ Inactive API key → 401
- ✅ Insufficient scopes → 403

## Maintenance

### Updating the Test API Key

If you need to update the test API key:

```bash
# Delete existing secret
kubectl delete secret simple-kanban-test-api-key -n apps-dev

# Create new secret with updated key
kubectl create secret generic simple-kanban-test-api-key -n apps-dev \
  --from-literal=api-key="NEW_API_KEY_HERE" \
  --from-literal=key-name="dev" \
  --from-literal=user-id="1" \
  --from-literal=scopes="read,write,docs,admin"
```

### Creating Additional Test API Keys

To create API keys for different test scenarios:

```bash
# Create API key via API (requires existing authentication)
curl -X POST https://kanban.stormpath.dev/api/api-keys/ \
  -H "Authorization: Bearer $EXISTING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-key-limited",
    "description": "Limited scope test key",
    "scopes": ["read"],
    "expires_in_days": 30
  }'
```

## Integration with CI/CD

The test script can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Test API Key Authentication
  run: |
    kubectl config set-context --current --namespace=apps-dev
    ./scripts/test-api-key.sh
```

## Troubleshooting

### Common Issues

1. **Secret not found**: Ensure you're in the correct namespace (`apps-dev`)
2. **API key expired**: Check expiration date and create a new key if needed
3. **Permission denied**: Verify the API key has the required scopes
4. **Database connection**: Ensure the application is running and database is accessible

### Debug Commands

```bash
# Check secret exists
kubectl get secret simple-kanban-test-api-key -n apps-dev

# View secret contents (base64 encoded)
kubectl get secret simple-kanban-test-api-key -n apps-dev -o yaml

# Check application logs
kubectl logs -f deployment/simple-kanban-dev -n apps-dev

# Test basic connectivity
curl -I https://kanban.stormpath.dev/health
```
