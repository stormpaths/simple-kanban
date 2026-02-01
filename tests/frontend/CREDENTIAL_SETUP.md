# Frontend Test Credential Setup

## Overview

Frontend tests require valid user credentials to test authenticated functionality. This guide explains how to set up and manage test credentials.

## Quick Start

### Automated Setup (Recommended)

Run the setup script to automatically create a test user and configure credentials:

```bash
./scripts/setup-frontend-tests.sh
```

This will:
1. ✅ Create a new test user via the API
2. ✅ Save credentials in multiple formats
3. ✅ Update docker-compose.yml
4. ✅ Verify the credentials work

### Manual Setup

If you prefer to use an existing user or create one manually:

```bash
# Set environment variables
export TEST_USERNAME="your-email@example.com"
export TEST_PASSWORD="your-password"

# Run tests
cd tests/frontend
docker-compose run --rm frontend-tests
```

---

## Credential Files

The setup script creates multiple credential files for different use cases:

### 1. `test-credentials.env` (Shell Script)
**Use:** Source in shell scripts or terminal

```bash
source tests/frontend/test-credentials.env
echo $TEST_USERNAME
```

### 2. `.env.test` (Docker Compose)
**Use:** Docker Compose environment file

```bash
docker-compose --env-file .env.test up
```

### 3. `test_credentials.py` (Python Module)
**Use:** Import in Python/pytest

```python
from test_credentials import TEST_USERNAME, TEST_PASSWORD
```

### 4. `test-credentials.json` (JSON)
**Use:** Parse in scripts or CI/CD

```bash
jq -r '.username' test-credentials.json
```

---

## How It Works

### Credential Loading Priority

The test fixtures (`conftest.py`) load credentials in this order:

1. **Environment variables** (highest priority)
   ```bash
   export TEST_USERNAME="user@example.com"
   export TEST_PASSWORD="password"
   ```

2. **Credentials file** (`test_credentials.py`)
   - Automatically loaded if environment variables not set
   - Created by `setup-frontend-tests.sh`

3. **Error** if neither found
   - Provides helpful message to run setup script

### Example Flow

```python
# In conftest.py
@pytest.fixture(scope="session")
def test_username() -> str:
    # Try environment variable first
    username = os.getenv("TEST_USERNAME")
    
    # Fall back to credentials file
    if not username:
        from test_credentials import TEST_USERNAME
        username = TEST_USERNAME
    
    return username
```

---

## Usage Examples

### Run All Tests

```bash
# With setup script (credentials auto-loaded)
./scripts/setup-frontend-tests.sh
cd tests/frontend
docker-compose run --rm frontend-tests

# With environment variables
export TEST_USERNAME="user@example.com"
export TEST_PASSWORD="password"
cd tests/frontend
docker-compose run --rm frontend-tests
```

### Run Specific Test

```bash
cd tests/frontend
docker-compose run --rm frontend-tests pytest test_authentication.py -v
```

### Run with Different Credentials

```bash
# Override default credentials
TEST_USERNAME="other@example.com" TEST_PASSWORD="other-pass" \
docker-compose run --rm frontend-tests
```

---

## Creating Test Users

### Option 1: Automated (Recommended)

```bash
./scripts/setup-frontend-tests.sh
```

### Option 2: Manual via API

```bash
curl -X POST https://kanban.stormpath.dev/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "TestPassword123!",
    "full_name": "Test User"
  }'
```

### Option 3: Manual via UI

1. Navigate to https://kanban.stormpath.dev
2. Click "Sign Up"
3. Fill in registration form
4. Use those credentials in tests

---

## Troubleshooting

### Problem: "TEST_USERNAME not found"

**Solution:** Run the setup script

```bash
./scripts/setup-frontend-tests.sh
```

### Problem: "Login failed" in tests

**Possible causes:**
1. User doesn't exist
2. Password incorrect
3. User was deleted

**Solution:** Create a new test user

```bash
./scripts/setup-frontend-tests.sh --force
```

### Problem: Credentials file not found

**Check:**
```bash
ls -la tests/frontend/test-credentials.*
```

**Solution:**
```bash
./scripts/setup-frontend-tests.sh
```

### Problem: Docker not picking up credentials

**Solution:** Rebuild the container

```bash
cd tests/frontend
docker-compose build --no-cache frontend-tests
```

---

## Security Notes

### ⚠️ Important

1. **Never commit credentials to git**
   - All credential files are in `.gitignore`
   - Double-check before committing

2. **Use test-only credentials**
   - Don't use production user credentials
   - Create dedicated test users

3. **Rotate credentials regularly**
   - Run setup script to create new users
   - Old users can be deleted from admin panel

### Credential Files in .gitignore

```gitignore
# Test credentials - DO NOT COMMIT
test-credentials.env
.env.test
test_credentials.py
test-credentials.json
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Setup Frontend Tests
  run: |
    ./scripts/setup-frontend-tests.sh --base-url ${{ secrets.TEST_BASE_URL }}

- name: Run Frontend Tests
  run: |
    cd tests/frontend
    docker-compose run --rm frontend-tests
```

### GitLab CI Example

```yaml
frontend-tests:
  script:
    - ./scripts/setup-frontend-tests.sh --base-url $TEST_BASE_URL
    - cd tests/frontend
    - docker-compose run --rm frontend-tests
```

---

## Advanced Usage

### Custom Base URL

```bash
./scripts/setup-frontend-tests.sh --base-url https://staging.example.com
```

### Force New User Creation

```bash
./scripts/setup-frontend-tests.sh --force
```

### Verify Credentials

```bash
cd tests/frontend
python3 setup_test_user.py --verify
```

### Use Existing Credentials

```bash
# Copy existing credentials
cp /path/to/existing/test-credentials.env tests/frontend/

# Or set environment variables
export TEST_USERNAME="existing@example.com"
export TEST_PASSWORD="existing-password"
```

---

## Summary

✅ **Automated setup** - One command to create and configure  
✅ **Multiple formats** - Shell, Docker, Python, JSON  
✅ **Flexible loading** - Environment variables or files  
✅ **Secure** - Credentials never committed to git  
✅ **CI/CD ready** - Easy integration with pipelines  

**Run this to get started:**
```bash
./scripts/setup-frontend-tests.sh
```
