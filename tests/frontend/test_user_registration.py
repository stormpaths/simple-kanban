"""
User Registration and Temporary Test User Creation

This module provides functionality to create temporary test users
for automated testing without requiring pre-existing credentials.
"""

import pytest
import time
from playwright.sync_api import Page, expect


def generate_test_user():
    """Generate unique test user credentials."""
    timestamp = int(time.time())
    return {
        "username": f"testuser_{timestamp}",
        "email": f"testuser_{timestamp}@example.com",
        "password": "TestPassword123!",
        "full_name": f"Test User {timestamp}"
    }


def test_user_registration_flow(page: Page, base_url: str):
    """
    Test user registration and verify account creation.
    
    This test creates a temporary user that can be used for other tests.
    """
    page.goto(base_url)
    
    # Wait for auth screen
    page.wait_for_selector("#auth-screen", timeout=10000)
    
    # Click to show signup form
    page.click("#show-signup")
    
    # Wait for signup form to appear
    page.wait_for_selector("#signup-form", state="visible", timeout=5000)
    
    # Generate test user
    user = generate_test_user()
    print(f"\n=== Creating Test User ===")
    print(f"Username: {user['username']}")
    print(f"Email: {user['email']}")
    
    # Fill registration form
    page.fill("#signup-username", user["username"])
    page.fill("#signup-email", user["email"])
    page.fill("#signup-fullname", user["full_name"])
    page.fill("#signup-password", user["password"])
    page.fill("#signup-confirm-password", user["password"])
    
    # Submit registration
    page.click("#signup-email-form button[type='submit']")
    
    # Wait for successful registration (should redirect to main app or show success)
    # The app might auto-login after registration
    page.wait_for_timeout(3000)
    
    # Check if we're logged in (board selector appears)
    try:
        page.wait_for_selector("#board-select", timeout=5000)
        print("✅ Registration successful - auto-logged in")
        expect(page.locator("#board-select")).to_be_visible()
    except:
        # Might need to login manually
        print("⚠️ Registration successful - attempting manual login")
        
        # Wait for page to settle
        page.wait_for_timeout(2000)
        
        # If still on signup form, click to show login
        if page.locator("#signup-form").is_visible():
            print("Still on signup form, switching to login...")
            page.click("#show-login")
            page.wait_for_selector("#login-form", state="visible", timeout=5000)
        
        # Check if we're on login form
        if page.locator("#login-form").is_visible():
            print("On login form, filling credentials...")
            page.fill("#login-email", user["email"])
            page.fill("#login-password", user["password"])
            page.click("#login-email-form button[type='submit']")
            
            # Wait for login
            try:
                page.wait_for_selector("#board-select", timeout=10000)
                print("✅ Login successful with new account")
                expect(page.locator("#board-select")).to_be_visible()
            except:
                # Take screenshot for debugging
                page.screenshot(path="test-results/registration-login-failed.png")
                print(f"❌ Login failed after registration")
                print(f"Current URL: {page.url}")
                print(f"Login form visible: {page.locator('#login-form').is_visible()}")
                
                # Check for error messages
                notification = page.locator("#notification")
                if notification.is_visible():
                    error_msg = page.locator("#notification-message").text_content()
                    print(f"Error notification: {error_msg}")
                
                # Check page content for errors
                page_content = page.content()
                if "error" in page_content.lower():
                    print("Page contains 'error' text")
                
                # Try to find any visible error elements
                error_elements = page.locator(".error, .alert-danger, .text-danger").all()
                for elem in error_elements:
                    if elem.is_visible():
                        print(f"Error element found: {elem.text_content()}")
                
                raise
        else:
            # Not on login form, check where we are
            page.screenshot(path="test-results/registration-unknown-state.png")
            print(f"Unknown state after registration")
            print(f"Current URL: {page.url}")
            print(f"Auth screen visible: {page.locator('#auth-screen').is_visible()}")
            print(f"Main app visible: {page.locator('#main-app').is_visible()}")
            
            # If we're still on signup form, registration might have failed
            if page.locator("#signup-form").is_visible():
                print("❌ Still on signup form - registration may have failed")
                # Check for error messages
                error_text = page.locator(".error, .alert, .notification").text_content() if page.locator(".error, .alert, .notification").count() > 0 else "No error message found"
                print(f"Error: {error_text}")
            
            raise Exception("Could not determine state after registration")
    
    # Save credentials for other tests to use
    print(f"\n=== Test User Created Successfully ===")
    print(f"Email: {user['email']}")
    print(f"Password: {user['password']}")
    print("These credentials can be used for subsequent tests")


@pytest.fixture
def temp_test_user(page: Page, base_url: str):
    """
    Fixture that creates a temporary test user and returns credentials.
    
    This can be used by other tests that need a fresh user account.
    """
    page.goto(base_url)
    
    # Navigate to signup
    page.wait_for_selector("#auth-screen", timeout=10000)
    page.click("#show-signup")
    page.wait_for_selector("#signup-form", state="visible", timeout=5000)
    
    # Generate and create user
    user = generate_test_user()
    
    page.fill("#signup-username", user["username"])
    page.fill("#signup-email", user["email"])
    page.fill("#signup-fullname", user["full_name"])
    page.fill("#signup-password", user["password"])
    page.fill("#signup-confirm-password", user["password"])
    
    page.click("#signup-email-form button[type='submit']")
    page.wait_for_timeout(3000)
    
    # Return credentials for use in tests
    return user


def test_registration_with_duplicate_email(page: Page, base_url: str):
    """Test that registration fails with duplicate email."""
    page.goto(base_url)
    
    # Create first user
    page.wait_for_selector("#auth-screen", timeout=10000)
    page.click("#show-signup")
    page.wait_for_selector("#signup-form", state="visible", timeout=5000)
    
    user = generate_test_user()
    
    page.fill("#signup-username", user["username"])
    page.fill("#signup-email", user["email"])
    page.fill("#signup-fullname", user["full_name"])
    page.fill("#signup-password", user["password"])
    page.fill("#signup-confirm-password", user["password"])
    
    page.click("#signup-email-form button[type='submit']")
    page.wait_for_timeout(2000)
    
    # Logout if auto-logged in
    if page.locator("#user-logout").is_visible():
        page.click("#user-logout")
        page.wait_for_selector("#auth-screen", timeout=5000)
    
    # Try to register again with same email
    page.click("#show-signup")
    page.wait_for_selector("#signup-form", state="visible", timeout=5000)
    
    page.fill("#signup-username", f"{user['username']}_2")
    page.fill("#signup-email", user["email"])  # Same email
    page.fill("#signup-fullname", user["full_name"])
    page.fill("#signup-password", user["password"])
    page.fill("#signup-confirm-password", user["password"])
    
    page.click("#signup-email-form button[type='submit']")
    page.wait_for_timeout(2000)
    
    # Should still be on signup form (registration failed)
    expect(page.locator("#signup-form")).to_be_visible()


def test_registration_password_mismatch(page: Page, base_url: str):
    """Test that registration fails when passwords don't match."""
    page.goto(base_url)
    
    page.wait_for_selector("#auth-screen", timeout=10000)
    page.click("#show-signup")
    page.wait_for_selector("#signup-form", state="visible", timeout=5000)
    
    user = generate_test_user()
    
    page.fill("#signup-username", user["username"])
    page.fill("#signup-email", user["email"])
    page.fill("#signup-fullname", user["full_name"])
    page.fill("#signup-password", user["password"])
    page.fill("#signup-confirm-password", "DifferentPassword123!")  # Mismatch
    
    page.click("#signup-email-form button[type='submit']")
    page.wait_for_timeout(2000)
    
    # Should still be on signup form
    expect(page.locator("#signup-form")).to_be_visible()
