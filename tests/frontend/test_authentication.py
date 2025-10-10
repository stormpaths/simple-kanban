"""
Authentication Flow Tests

Tests for login, logout, and authentication state management.
"""

import pytest
from playwright.sync_api import Page, expect


class TestAuthentication:
    """Test suite for authentication flows."""

    def test_login_with_valid_credentials(
        self, page: Page, base_url: str, test_username: str, test_password: str
    ):
        """Test successful login with valid credentials."""
        page.goto(base_url)

        # Wait for login form
        page.wait_for_selector("#login-form", timeout=10000)

        # Fill credentials
        page.fill("#login-email", test_username)
        page.fill("#login-password", test_password)

        # Submit login
        page.click("#login-email-form button[type='submit']")

        # Verify successful login - board selector should be visible
        page.wait_for_selector("#board-select", timeout=10000)
        expect(page.locator("#board-select")).to_be_visible()

        # Verify user menu button is visible (logout is in dropdown)
        expect(page.locator("#user-menu-btn")).to_be_visible()

        # Verify logout link exists (even if hidden in dropdown)
        expect(page.locator("#user-logout")).to_be_attached()

    def test_login_with_invalid_credentials(self, page: Page, base_url: str):
        """Test login failure with invalid credentials."""
        page.goto(base_url)

        # Wait for login form
        page.wait_for_selector("#login-form", timeout=10000)

        # Fill invalid credentials
        page.fill("#login-email", "invalid@example.com")
        page.fill("#login-password", "wrong_password")

        # Submit login
        page.click("#login-email-form button[type='submit']")

        # Should show error message or stay on login page
        page.wait_for_timeout(2000)

        # Verify still on login page (no board selector)
        expect(page.locator("#login-form")).to_be_visible()

    def test_logout_functionality(self, authenticated_page: Page):
        """Test logout functionality."""
        page = authenticated_page

        # Verify logged in
        expect(page.locator("#board-select")).to_be_visible()

        # Open user menu dropdown
        page.click("#user-menu-btn")
        page.wait_for_timeout(500)

        # Verify logout is now visible
        expect(page.locator("#user-logout")).to_be_visible()

        # Click logout
        page.click("#user-logout")

        # Should redirect to login page
        page.wait_for_selector("#login-form", timeout=10000)
        expect(page.locator("#login-form")).to_be_visible()

    def test_session_persistence(self, authenticated_page: Page, base_url: str):
        """Test that session persists across page reloads."""
        page = authenticated_page

        # Verify logged in
        expect(page.locator("#board-select")).to_be_visible()

        # Reload page
        page.reload()

        # Should still be logged in - board selector should reappear
        page.wait_for_selector("#board-select", timeout=10000)
        expect(page.locator("#board-select")).to_be_visible()

        # Verify user menu is still visible
        expect(page.locator("#user-menu-btn")).to_be_visible()

    def test_protected_page_redirect(self, page: Page, base_url: str):
        """Test that accessing protected pages redirects to login."""
        # Try to access main app without authentication
        page.goto(base_url)

        # Should show login form
        page.wait_for_selector("#login-form", timeout=10000)
        expect(page.locator("#login-form")).to_be_visible()
