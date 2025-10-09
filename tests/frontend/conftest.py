"""
Playwright Test Configuration for Simple Kanban Board

This module provides fixtures and configuration for frontend testing.
"""

import os
import time
import pytest
from playwright.sync_api import Page, Browser, BrowserContext
from typing import Generator


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get the base URL for testing from environment or use default."""
    return os.getenv("BASE_URL", "https://kanban.stormpath.dev")


@pytest.fixture(scope="session")
def test_credentials(base_url: str):
    """
    Get or create test user credentials.
    
    If TEST_USERNAME and TEST_PASSWORD are set, use those.
    Otherwise, create a temporary test user automatically.
    """
    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")
    
    if username and password:
        # Use provided credentials
        return {"email": username, "password": password, "created": False}
    
    # Create temporary user
    from playwright.sync_api import sync_playwright
    
    timestamp = int(time.time())
    temp_user = {
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@example.com",
        "password": "TestPassword123!",
        "full_name": f"Test User {timestamp}",
        "created": True
    }
    
    print(f"\n=== Creating Temporary Test User ===")
    print(f"Email: {temp_user['email']}")
    print(f"Password: {temp_user['password']}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        try:
            page.goto(base_url)
            page.wait_for_selector("#auth-screen", timeout=10000)
            page.click("#show-signup")
            page.wait_for_selector("#signup-form", state="visible", timeout=5000)
            
            page.fill("#signup-username", temp_user["username"])
            page.fill("#signup-email", temp_user["email"])
            page.fill("#signup-fullname", temp_user["full_name"])
            page.fill("#signup-password", temp_user["password"])
            page.fill("#signup-confirm-password", temp_user["password"])
            
            page.click("#signup-email-form button[type='submit']")
            page.wait_for_timeout(3000)
            
            print("✅ Temporary test user created successfully")
        except Exception as e:
            print(f"⚠️ Failed to create temporary user: {e}")
            print("Falling back to environment credentials")
            temp_user = {
                "email": "michael@stormpath.dev",
                "password": "TestPassword123!",
                "created": False
            }
        finally:
            browser.close()
    
    return temp_user


@pytest.fixture(scope="session")
def test_username() -> str:
    """
    Test user email (used as username for login).
    
    Tries to load credentials from:
    1. TEST_USERNAME environment variable
    2. test_credentials.py file (if exists)
    3. Raises error if neither found
    """
    username = os.getenv("TEST_USERNAME")
    
    # If not in env, try to load from credentials file
    if not username:
        try:
            from test_credentials import TEST_USERNAME
            username = TEST_USERNAME
            print(f"\n✅ Loaded credentials from test_credentials.py")
        except ImportError:
            pass
    
    if not username:
        print("\n⚠️  TEST_USERNAME not set. Please run setup:")
        print("   ./scripts/setup-frontend-tests.sh")
        print("\n   Or set manually:")
        print("   export TEST_USERNAME='your-email@example.com'")
        print("   export TEST_PASSWORD='your-password'\n")
        raise ValueError("TEST_USERNAME not found. Run ./scripts/setup-frontend-tests.sh")
    
    return username


@pytest.fixture(scope="session")
def test_password() -> str:
    """
    Test user password.
    
    Tries to load credentials from:
    1. TEST_PASSWORD environment variable
    2. test_credentials.py file (if exists)
    3. Raises error if neither found
    """
    password = os.getenv("TEST_PASSWORD")
    
    # If not in env, try to load from credentials file
    if not password:
        try:
            from test_credentials import TEST_PASSWORD
            password = TEST_PASSWORD
        except ImportError:
            pass
    
    if not password:
        raise ValueError("TEST_PASSWORD not found. Run ./scripts/setup-frontend-tests.sh")
    
    return password


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context with extended timeout and viewport."""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,  # For self-signed certs in dev
    }


@pytest.fixture
def authenticated_page(page: Page, base_url: str, test_username: str, test_password: str) -> Generator[Page, None, None]:
    """
    Provide an authenticated page session.
    
    This fixture logs in the user and provides a page ready for testing.
    It handles the authentication flow automatically.
    """
    # Navigate to login page
    page.goto(base_url)
    
    # Check if already logged in (board selector visible)
    if page.locator("#board-select").is_visible():
        yield page
        return
    
    # Wait for login form to be visible
    page.wait_for_selector("#login-form", timeout=10000)
    
    # Fill in login credentials (using email field)
    page.fill("#login-email", test_username)
    page.fill("#login-password", test_password)
    
    # Submit login form
    page.click("#login-email-form button[type='submit']")
    
    # Wait for successful login (board selector should appear)
    page.wait_for_selector("#board-select", timeout=10000)
    
    yield page
    
    # Cleanup: logout after test (open dropdown first)
    if page.locator("#user-menu-btn").is_visible():
        page.click("#user-menu-btn")
        page.wait_for_timeout(500)
        if page.locator("#user-logout").is_visible():
            page.click("#user-logout")


@pytest.fixture
def authenticated_context(context: BrowserContext, base_url: str, test_username: str, test_password: str) -> Generator[BrowserContext, None, None]:
    """
    Provide an authenticated browser context.
    
    Useful for tests that need multiple pages or tabs.
    """
    page = context.new_page()
    
    # Navigate and login
    page.goto(base_url)
    
    if not page.locator("#user-logout").is_visible():
        page.wait_for_selector("#login-form", timeout=10000)
        page.fill("#login-email", test_username)
        page.fill("#login-password", test_password)
        page.click("#login-email-form button[type='submit']")
        page.wait_for_selector("#board-select", timeout=10000)
    
    page.close()
    
    yield context


@pytest.fixture
def test_board_name() -> str:
    """Generate a unique test board name."""
    import time
    return f"Test Board {int(time.time())}"


@pytest.fixture
def cleanup_test_boards(authenticated_page: Page):
    """
    Cleanup fixture that removes test boards after tests.
    
    Yields before cleanup, allowing tests to run first.
    """
    created_board_ids = []
    
    def register_board(board_id: int):
        """Register a board ID for cleanup."""
        created_board_ids.append(board_id)
    
    yield register_board
    
    # Cleanup: Delete all created test boards
    for board_id in created_board_ids:
        try:
            # Use the page's evaluate to call API directly
            authenticated_page.evaluate(f"""
                fetch('/api/boards/{board_id}', {{
                    method: 'DELETE',
                    headers: {{
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    }}
                }})
            """)
        except Exception as e:
            print(f"Warning: Failed to cleanup board {board_id}: {e}")
