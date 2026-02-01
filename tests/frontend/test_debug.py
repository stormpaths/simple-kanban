"""
Debug test to check login flow and page state
"""

import pytest
from playwright.sync_api import Page


def test_debug_login_flow(page: Page):
    """Debug test to see what happens during login."""
    base_url = "https://kanban.stormpath.dev"
    test_email = "michael@stormpath.dev"
    test_password = "TestPassword123!"

    print(f"\n=== Debug Login Flow ===")
    print(f"URL: {base_url}")
    print(f"Email: {test_email}")

    # Navigate to page
    page.goto(base_url)
    print(f"Page loaded: {page.url}")

    # Wait for login form
    page.wait_for_selector("#login-form", timeout=10000)
    print("Login form found")

    # Take screenshot before login
    page.screenshot(path="test-results/before-login.png")
    print("Screenshot saved: before-login.png")

    # Fill credentials
    page.fill("#login-email", test_email)
    page.fill("#login-password", test_password)
    print("Credentials filled")

    # Submit form
    page.click("#login-email-form button[type='submit']")
    print("Login submitted")

    # Wait a bit
    page.wait_for_timeout(3000)

    # Take screenshot after login attempt
    page.screenshot(path="test-results/after-login.png")
    print(f"Screenshot saved: after-login.png")
    print(f"Current URL: {page.url}")

    # Check what's visible
    print("\n=== Checking page elements ===")
    print(f"Login form visible: {page.locator('#login-form').is_visible()}")
    print(f"Main app visible: {page.locator('#main-app').is_visible()}")
    print(f"Board select visible: {page.locator('#board-select').is_visible()}")
    print(f"Auth screen visible: {page.locator('#auth-screen').is_visible()}")

    # Get page content to see errors
    content = page.content()
    if "error" in content.lower() or "invalid" in content.lower():
        print("\n=== Possible error on page ===")
        # Try to find error messages
        error_elements = page.locator(".error, .alert, .notification").all()
        for elem in error_elements:
            if elem.is_visible():
                print(f"Error element: {elem.text_content()}")

    print("\n=== End Debug ===")

    # This test is just for debugging, so we'll pass it
    assert True
