# Frontend Tests Setup Guide

## Prerequisites

Before running the frontend tests, you need to set up test credentials.

### 1. Create a Test User

You need a valid user account in your Simple Kanban application. You can either:

**Option A: Use an existing user**
- Use your own account credentials

**Option B: Create a dedicated test user**
```bash
# Register via the UI at https://kanban.stormpath.dev
# Or use the API:
curl -X POST https://kanban.stormpath.dev/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "YourSecurePassword123!",
    "full_name": "Test User"
  }'
```

### 2. Set Environment Variables

Set your test credentials as environment variables:

```bash
# In your shell or .env file
export TEST_USERNAME="your-email@example.com"  # Must be a valid email
export TEST_PASSWORD="YourActualPassword"
export BASE_URL="https://kanban.stormpath.dev"  # Optional, defaults to this
```

### 3. Run Tests

#### Using Docker (Recommended)
```bash
# Run all tests
./scripts/test-frontend-docker.sh

# Run with your credentials
TEST_USERNAME="your-email@example.com" TEST_PASSWORD="your-password" \
  ./scripts/test-frontend-docker.sh

# Run only modal tests
./scripts/test-frontend-docker.sh --modal

# Generate HTML report
./scripts/test-frontend-docker.sh --report
```

#### Using Poetry (Local)
```bash
cd tests/frontend

# Install dependencies
poetry install
poetry run playwright install chromium

# Run tests
TEST_USERNAME="your-email@example.com" TEST_PASSWORD="your-password" \
  poetry run pytest --browser chromium -v
```

### 4. Verify Setup

Run the debug test to verify your credentials work:

```bash
cd tests/frontend
docker-compose run --rm frontend-tests pytest test_debug.py -v -s
```

This will show you:
- Whether the login form is found
- Whether login succeeds
- What elements are visible after login
- Screenshots in `test-results/` directory

**Expected output if working:**
```
Login form visible: False
Main app visible: True
Board select visible: True
Auth screen visible: False
```

**If login fails:**
```
Login form visible: True  ← Still on login page
Main app visible: False
Board select visible: False
Auth screen visible: True
```

### Troubleshooting

#### Login Fails
- **Check credentials**: Verify email and password are correct
- **Check user exists**: Make sure the user is registered
- **Check password requirements**: Password must meet security requirements
- **Try manual login**: Test credentials in browser first

#### Tests Timeout
- **Check application is running**: Visit BASE_URL in browser
- **Check network**: Ensure Docker container can reach the application
- **Increase timeout**: Modify `timeout` values in test files if needed

#### Screenshots Not Saved
- **Check volume mounts**: Ensure `test-results/` directory exists
- **Check permissions**: Docker may need write permissions

### Test Credentials in CI/CD

For automated testing, set credentials as secrets:

**GitHub Actions:**
```yaml
env:
  TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
  TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
```

**GitLab CI:**
```yaml
variables:
  TEST_USERNAME: $TEST_USERNAME  # Set in CI/CD settings
  TEST_PASSWORD: $TEST_PASSWORD
```

### Security Notes

⚠️ **Never commit credentials to git**
- Use environment variables
- Add `.env` to `.gitignore`
- Use CI/CD secrets for automation
- Consider using a dedicated test account with limited permissions

### Next Steps

Once setup is complete:
1. Run `test_debug.py` to verify login works
2. Run authentication tests: `pytest test_authentication.py -v`
3. Run modal tests: `pytest test_task_modal_reusability.py -v`
4. Run full suite: `./scripts/test-frontend-docker.sh`

For more details, see [README.md](README.md)
