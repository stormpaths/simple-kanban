# Frontend Testing Suite

Comprehensive browser-based testing for the Simple Kanban Board using Playwright.

## Overview

This test suite validates the frontend UI interactions, focusing on:
- **Modal reusability** - Ensuring modals can be opened/edited multiple times
- **Task management** - Creating, editing, deleting tasks
- **Board management** - Creating, switching, editing boards
- **Authentication flows** - Login, logout, session persistence
- **User workflows** - End-to-end user scenarios

## Critical Tests

### Modal Reusability Tests (`test_task_modal_reusability.py`)
These tests specifically address the bug where **buttons stopped working after the first usage**:

- `test_create_and_edit_task_multiple_times` - **CRITICAL**: Tests editing a task 3+ times
- `test_modal_buttons_remain_functional` - Tests Save/Cancel/Delete buttons after multiple uses
- `test_edit_different_tasks_sequentially` - Tests switching between different task modals
- `test_rapid_modal_interactions` - Stress tests modal system with rapid open/close

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r tests/frontend/requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Running Tests

```bash
# Run all frontend tests
./scripts/test-frontend.sh

# Run with visible browser (for debugging)
./scripts/test-frontend.sh --headed

# Run only modal tests
./scripts/test-frontend.sh --modal

# Run with debugging enabled
./scripts/test-frontend.sh --debug

# Run smoke tests only (quick validation)
./scripts/test-frontend.sh --smoke
```

### Direct pytest Usage

```bash
cd tests/frontend

# Run all tests
pytest

# Run specific test file
pytest test_task_modal_reusability.py

# Run specific test
pytest test_task_modal_reusability.py::TestTaskModalReusability::test_create_and_edit_task_multiple_times

# Run with visible browser
pytest --headed

# Run with slow motion (for watching tests)
pytest --headed --slowmo 1000
```

## Test Structure

```
tests/frontend/
├── conftest.py                          # Pytest fixtures and configuration
├── pytest.ini                           # Pytest settings
├── requirements.txt                     # Python dependencies
├── test_authentication.py               # Login/logout tests
├── test_board_management.py             # Board and column tests
└── test_task_modal_reusability.py       # Modal interaction tests (CRITICAL)
```

## Fixtures

### `authenticated_page`
Provides a logged-in browser page ready for testing.

```python
def test_something(authenticated_page: Page):
    page = authenticated_page
    # Already logged in, ready to test
    page.click("#new-task-btn")
```

### `test_board_name`
Generates unique board names for tests.

```python
def test_create_board(authenticated_page: Page, test_board_name: str):
    # test_board_name is unique per test run
    page.fill("#board-name", test_board_name)
```

## Configuration

### Environment Variables

- `BASE_URL` - Application URL (default: https://kanban.stormpath.dev)
- `TEST_USERNAME` - Test user username (default: testuser)
- `TEST_PASSWORD` - Test user password (default: TestPassword123!)

### Example

```bash
export BASE_URL="https://kanban-staging.example.com"
export TEST_USERNAME="myuser"
export TEST_PASSWORD="mypassword"
./scripts/test-frontend.sh
```

## Test Markers

Tests can be marked with pytest markers for selective execution:

- `@pytest.mark.smoke` - Quick smoke tests
- `@pytest.mark.critical` - Critical functionality tests
- `@pytest.mark.modal` - Modal-related tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.slow` - Slow-running tests

### Running Specific Markers

```bash
# Run only smoke tests
pytest -m smoke

# Run everything except slow tests
pytest -m "not slow"

# Run critical and modal tests
pytest -m "critical or modal"
```

## Debugging Tests

### Visual Debugging

```bash
# Run with visible browser and slow motion
pytest --headed --slowmo 1000

# Run with debugging breakpoints
pytest --headed --pdb
```

### Screenshots and Videos

Playwright automatically captures screenshots on failure. To enable video recording:

```python
# In conftest.py, update browser_context_args:
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "record_video_dir": "test-results/videos",
    }
```

### Trace Viewer

For detailed debugging, enable trace recording:

```python
# In your test
page.context.tracing.start(screenshots=True, snapshots=True)
# ... test code ...
page.context.tracing.stop(path="trace.zip")
```

View trace:
```bash
playwright show-trace trace.zip
```

## Common Issues

### Browser Not Found
```bash
# Install Playwright browsers
playwright install chromium
```

### Connection Refused
- Ensure the application is running at BASE_URL
- Check if you need to set up port forwarding for local testing

### Authentication Failures
- Verify TEST_USERNAME and TEST_PASSWORD are correct
- Check if test user exists in the database
- Run bootstrap script if needed: `./scripts/test-bootstrap.sh`

### Modal Tests Failing
If modal tests fail, this indicates the **exact bug we're trying to catch**:
- Buttons not working after first use
- Modal state not resetting properly
- Event listeners not being cleaned up

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Frontend Tests

on: [push, pull_request]

jobs:
  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r tests/frontend/requirements.txt
          playwright install --with-deps chromium
      
      - name: Run frontend tests
        env:
          BASE_URL: ${{ secrets.TEST_BASE_URL }}
          TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: ./scripts/test-frontend.sh
      
      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: tests/frontend/test-results/
```

## Best Practices

1. **Use auto-waiting** - Playwright waits automatically, avoid explicit sleeps
2. **Test user workflows** - Test complete user scenarios, not just individual actions
3. **Keep tests independent** - Each test should work in isolation
4. **Clean up test data** - Use fixtures to clean up created boards/tasks
5. **Use meaningful assertions** - Use `expect()` with clear messages
6. **Test error scenarios** - Don't just test happy paths

## Writing New Tests

### Template

```python
def test_my_feature(authenticated_page: Page):
    """Test description explaining what this validates."""
    page = authenticated_page
    
    # Arrange - Set up test data
    page.click("#new-task-btn")
    
    # Act - Perform the action
    page.fill("#task-title", "Test Task")
    page.click("#save-task-btn")
    
    # Assert - Verify the result
    expect(page.locator(".task-card")).to_contain_text("Test Task")
```

## Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Best Practices](https://playwright.dev/python/docs/best-practices)

## Support

For issues or questions:
1. Check test output for detailed error messages
2. Run with `--headed` to see what's happening
3. Enable trace recording for detailed debugging
4. Review Playwright documentation for API details
