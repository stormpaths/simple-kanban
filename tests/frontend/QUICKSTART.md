# Frontend Tests - Quick Start

## TL;DR - Run Tests in 2 Minutes

### Option 1: Use Existing Account (Recommended)

If you have an account on https://kanban.stormpath.dev:

```bash
# Set your credentials
export TEST_USERNAME="your-email@example.com"
export TEST_PASSWORD="your-password"

# Run all tests
./scripts/test-frontend-docker.sh
```

### Option 2: Create Test Account First

1. **Register a test account:**
   - Visit https://kanban.stormpath.dev
   - Click "Sign up"
   - Use email: `test-<yourname>@example.com`
   - Password: `TestPassword123!`

2. **Run tests with your new account:**
   ```bash
   export TEST_USERNAME="test-yourname@example.com"
   export TEST_PASSWORD="TestPassword123!"
   ./scripts/test-frontend-docker.sh
   ```

### Option 3: Use .env File

Create `tests/frontend/.env`:
```bash
TEST_USERNAME=your-email@example.com
TEST_PASSWORD=your-password
BASE_URL=https://kanban.stormpath.dev
```

Then run:
```bash
./scripts/test-frontend-docker.sh
```

## What Gets Tested

✅ **Modal Reusability** (8 tests) - Your button bug  
✅ **Authentication** (5 tests) - Login/logout flows  
✅ **Board Management** (7 tests) - CRUD operations  
✅ **User Registration** (3 tests) - Signup validation  

**Total: 23 comprehensive UI tests**

## Test Modes

```bash
# All tests (~2-3 minutes)
./scripts/test-frontend-docker.sh

# Only modal tests (the bug you're fixing)
./scripts/test-frontend-docker.sh --modal

# With HTML report
./scripts/test-frontend-docker.sh --report

# Rebuild container
./scripts/test-frontend-docker.sh --build

# Debug shell
./scripts/test-frontend-docker.sh --shell
```

## Troubleshooting

### "Login failed" or tests timeout
- **Check credentials**: Make sure email and password are correct
- **Test manually**: Try logging in at https://kanban.stormpath.dev
- **Check password**: Must meet requirements (uppercase, lowercase, number, special char)

### "Docker not found"
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
```

### "Permission denied"
```bash
# Add your user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Tests are slow
- First run downloads browser (~500MB) - subsequent runs are fast
- Use `--modal` flag to run only the tests you care about

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Frontend Tests
  env:
    TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
    TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
  run: ./scripts/test-frontend-docker.sh
```

### GitLab CI
```yaml
frontend-tests:
  script:
    - ./scripts/test-frontend-docker.sh
  variables:
    TEST_USERNAME: $TEST_USERNAME
    TEST_PASSWORD: $TEST_PASSWORD
```

## Need Help?

1. **Run debug test**: `./scripts/test-frontend-docker.sh --shell` then `pytest test_debug.py -v -s`
2. **Check logs**: Look in `tests/frontend/test-results/` for screenshots
3. **See full docs**: Read `tests/frontend/README.md`

## Success Looks Like

```
======================== test session starts =========================
test_authentication.py::test_login ✓
test_authentication.py::test_logout ✓
test_board_management.py::test_create_board ✓
test_task_modal_reusability.py::test_modal_buttons ✓
...
===================== 23 passed in 45.2s ========================
✅ All frontend tests passed!
```

**That's it! Your modal button bug will be caught automatically.** 🎉
