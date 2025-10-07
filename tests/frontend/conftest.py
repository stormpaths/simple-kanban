"""
Playwright Test Configuration for Simple Kanban Board

This module provides fixtures and configuration for frontend testing.
"""

import os
import pytest
from playwright.sync_api import Page, Browser, BrowserContext
from typing import Generator


@pytest.fixture(scope="session")
def base_url() -> str:
    """Get the base URL for testing from environment or use default."""
    return os.getenv("BASE_URL", "https://kanban.stormpath.dev")


@pytest.fixture(scope="session")
def test_username() -> str:
    """Test user email (used as username for login)."""
    # Note: The login form uses email, not username
    return os.getenv("TEST_USERNAME", "michael@stormpath.dev")


@pytest.fixture(scope="session")
def test_password() -> str:
    """Test user password."""
    return os.getenv("TEST_PASSWORD", "TestPassword123!")


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
    
    # Check if already logged in (has user menu)
    if page.locator("#user-logout").is_visible():
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
    
    # Cleanup: logout after test
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
