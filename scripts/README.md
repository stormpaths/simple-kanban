# Simple Kanban Board - Test Scripts

This directory contains comprehensive test scripts for validating the Simple Kanban Board application after deployment.

## Test Scripts Overview

### Individual Test Scripts
- **`test-api-key.sh`** - Tests API key authentication and core endpoints
- **`test-admin.sh`** - Tests admin functionality and statistics
- **`test-groups.sh`** - Tests group management and board sharing

### Comprehensive Test Battery
- **`test-all.sh`** - Runs all tests with unified reporting

## Usage

### Quick Post-Deployment Validation
```bash
# Run all tests (recommended after deployment)
./scripts/test-all.sh

# Quick smoke test (faster, skips comprehensive tests)
./scripts/test-all.sh --quick

# Verbose output (see detailed test execution)
./scripts/test-all.sh --verbose

# Stop on first failure (for debugging)
./scripts/test-all.sh --stop-on-fail
```

### Individual Test Execution
```bash
# Test specific functionality
./scripts/test-api-key.sh    # API key authentication
./scripts/test-admin.sh      # Admin functionality  
./scripts/test-groups.sh     # Group management
```

## Test Results

### Console Output
The test battery provides color-coded console output:
- ✅ **Green** - Tests passed
- ❌ **Red** - Tests failed  
- ⚠️ **Yellow** - Warnings or skipped tests
- ℹ️ **Blue** - Information messages

### Machine-Readable Report
After execution, a JSON report is generated at `test-results.json`:
```json
{
  "timestamp": "2025-10-04T10:31:47-07:00",
  "duration": 45,
  "mode": "full",
  "summary": {
    "total": 8,
    "passed": 8,
    "failed": 0,
    "skipped": 0
  },
  "success": true,
  "results": [...]
}
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Post-Deployment Tests
  run: |
    ./scripts/test-all.sh --stop-on-fail
    if [ $? -ne 0 ]; then
      echo "Deployment validation failed"
      exit 1
    fi
```

### Kubernetes Job Example
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: kanban-test-battery
spec:
  template:
    spec:
      containers:
      - name: test-runner
        image: your-test-image
        command: ["./scripts/test-all.sh", "--quick"]
```

## Test Coverage

### Current Coverage
- ✅ **Authentication** - API key and JWT validation
- ✅ **Core APIs** - Board, task, and user management
- ✅ **Admin Functions** - Statistics and user management
- ✅ **Group Management** - Board sharing and access control
- ✅ **Security** - Authorization and input validation
- ✅ **Static Assets** - File serving and documentation
- ✅ **Health Checks** - Application availability

### Future Extensions
As you add features, extend the test battery:
```bash
# Example future tests
./scripts/test-websockets.sh     # Real-time features
./scripts/test-notifications.sh  # Email/push notifications
./scripts/test-uploads.sh        # File attachment features
./scripts/test-reports.sh        # Analytics and reporting
```

## Prerequisites

### Required Tools
- `curl` - HTTP requests
- `jq` - JSON parsing
- `kubectl` - Kubernetes access (for API key retrieval)
- `base64` - Secret decoding

### Required Secrets
The tests require the Kubernetes secret `simple-kanban-test-api-key` in the `apps-dev` namespace containing:
- `api-key` - Base64 encoded API key
- `key-name` - API key name
- `user-id` - Associated user ID
- `scopes` - API key scopes

## Troubleshooting

### Common Issues

**API Key Not Found**
```bash
# Check if secret exists
kubectl get secret simple-kanban-test-api-key -n apps-dev

# Recreate if missing
kubectl create secret generic simple-kanban-test-api-key -n apps-dev \
  --from-literal=api-key="your-api-key" \
  --from-literal=key-name="dev" \
  --from-literal=user-id="1" \
  --from-literal=scopes="read,write,docs,admin"
```

**Application Not Responding**
```bash
# Check deployment status
kubectl get deployment simple-kanban-dev -n apps-dev

# Check pod logs
kubectl logs -n apps-dev deployment/simple-kanban-dev
```

**Permission Denied**
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

## Best Practices

### Post-Deployment Workflow
1. **Deploy** your changes
2. **Wait** for deployment to stabilize
3. **Run** `./scripts/test-all.sh` 
4. **Verify** all tests pass before promoting to production
5. **Archive** test results for audit trail

### Development Workflow
1. **Develop** new features
2. **Add** corresponding test cases
3. **Run** individual tests during development
4. **Run** full test battery before committing
5. **Ensure** CI/CD pipeline includes test validation

This comprehensive test battery ensures your Simple Kanban Board remains stable and functional as you continue to add features and improvements!
