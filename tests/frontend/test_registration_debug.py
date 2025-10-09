"""
Debug registration to see exactly what's happening
"""

import pytest
import time
from playwright.sync_api import Page


def test_registration_detailed_debug(page: Page):
    """Detailed debug of registration flow."""
    base_url = "https://kanban.stormpath.dev"
    
    timestamp = int(time.time())
    user = {
        "username": f"debuguser_{timestamp}",
        "email": f"debuguser_{timestamp}@example.com",
        "password": "TestPassword123!",
        "full_name": f"Debug User {timestamp}"
    }
    
    print(f"\n{'='*60}")
    print(f"REGISTRATION DEBUG TEST")
    print(f"{'='*60}")
    print(f"Username: {user['username']}")
    print(f"Email: {user['email']}")
    print(f"Password: {user['password']}")
    print(f"{'='*60}\n")
    
    # Navigate to page
    print("Step 1: Navigate to page...")
    page.goto(base_url)
    print(f"  ✓ Current URL: {page.url}")
    
    # Wait for auth screen
    print("\nStep 2: Wait for auth screen...")
    page.wait_for_selector("#auth-screen", timeout=10000)
    print("  ✓ Auth screen found")
    
    # Take screenshot before signup
    page.screenshot(path="test-results/01-before-signup.png")
    print("  ✓ Screenshot: 01-before-signup.png")
    
    # Click signup
    print("\nStep 3: Click 'Sign up' link...")
    page.click("#show-signup")
    page.wait_for_timeout(1000)
    print("  ✓ Clicked signup link")
    
    # Wait for signup form
    print("\nStep 4: Wait for signup form...")
    page.wait_for_selector("#signup-form", state="visible", timeout=5000)
    print("  ✓ Signup form visible")
    
    # Take screenshot of signup form
    page.screenshot(path="test-results/02-signup-form.png")
    print("  ✓ Screenshot: 02-signup-form.png")
    
    # Fill form
    print("\nStep 5: Fill registration form...")
    page.fill("#signup-username", user["username"])
    print(f"  ✓ Username filled: {user['username']}")
    
    page.fill("#signup-email", user["email"])
    print(f"  ✓ Email filled: {user['email']}")
    
    page.fill("#signup-fullname", user["full_name"])
    print(f"  ✓ Full name filled: {user['full_name']}")
    
    page.fill("#signup-password", user["password"])
    print(f"  ✓ Password filled")
    
    page.fill("#signup-confirm-password", user["password"])
    print(f"  ✓ Confirm password filled")
    
    # Take screenshot with filled form
    page.screenshot(path="test-results/03-form-filled.png")
    print("  ✓ Screenshot: 03-form-filled.png")
    
    # Listen for network requests
    print("\nStep 6: Submit registration form...")
    
    # Set up request/response listeners
    registration_request = None
    registration_response = None
    
    def handle_request(request):
        nonlocal registration_request
        if "/api/auth/register" in request.url:
            registration_request = request
            print(f"  → Request to: {request.url}")
            print(f"  → Method: {request.method}")
            print(f"  → Headers: {request.headers}")
            try:
                print(f"  → Body: {request.post_data}")
            except:
                pass
    
    def handle_response(response):
        nonlocal registration_response
        if "/api/auth/register" in response.url:
            registration_response = response
            print(f"  ← Response status: {response.status}")
            print(f"  ← Response headers: {response.headers}")
            try:
                body = response.text()
                print(f"  ← Response body: {body[:500]}")
            except:
                pass
    
    page.on("request", handle_request)
    page.on("response", handle_response)
    
    # Submit form
    page.click("#signup-email-form button[type='submit']")
    print("  ✓ Clicked submit button")
    
    # Wait for response
    print("\nStep 7: Wait for registration response...")
    page.wait_for_timeout(5000)
    
    # Take screenshot after submit
    page.screenshot(path="test-results/04-after-submit.png")
    print("  ✓ Screenshot: 04-after-submit.png")
    
    # Check what's visible
    print("\nStep 8: Check page state...")
    print(f"  Login form visible: {page.locator('#login-form').is_visible()}")
    print(f"  Signup form visible: {page.locator('#signup-form').is_visible()}")
    print(f"  Auth screen visible: {page.locator('#auth-screen').is_visible()}")
    print(f"  Main app visible: {page.locator('#main-app').is_visible()}")
    print(f"  Board select visible: {page.locator('#board-select').is_visible()}")
    
    # Check for notifications
    print("\nStep 9: Check for notifications/errors...")
    notification = page.locator("#notification")
    if notification.is_visible():
        msg = page.locator("#notification-message").text_content()
        print(f"  ⚠️ Notification: {msg}")
    else:
        print("  No notification visible")
    
    # Check console logs
    print("\nStep 10: Check console logs...")
    # Note: Console logs are captured automatically by Playwright
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if registration_request:
        print("✓ Registration request was sent")
    else:
        print("✗ No registration request detected")
    
    if registration_response:
        print(f"✓ Got response with status: {registration_response.status}")
        if registration_response.status == 201:
            print("  ✓ Registration successful (201 Created)")
        elif registration_response.status == 200:
            print("  ✓ Registration successful (200 OK)")
        else:
            print(f"  ✗ Registration failed with status {registration_response.status}")
    else:
        print("✗ No registration response detected")
    
    # Now try to login
    print(f"\n{'='*60}")
    print("ATTEMPTING LOGIN WITH NEW ACCOUNT")
    print(f"{'='*60}\n")
    
    # Check if we need to switch to login form
    if page.locator("#signup-form").is_visible():
        print("Step 11: Switch to login form...")
        page.click("#show-login")
        page.wait_for_selector("#login-form", state="visible", timeout=5000)
        print("  ✓ Switched to login form")
    
    if page.locator("#login-form").is_visible():
        print("\nStep 12: Fill login form...")
        page.fill("#login-email", user["email"])
        print(f"  ✓ Email filled: {user['email']}")
        
        page.fill("#login-password", user["password"])
        print(f"  ✓ Password filled")
        
        # Take screenshot before login
        page.screenshot(path="test-results/05-before-login.png")
        print("  ✓ Screenshot: 05-before-login.png")
        
        # Set up login listeners
        login_request = None
        login_response = None
        
        def handle_login_request(request):
            nonlocal login_request
            if "/api/auth/login" in request.url:
                login_request = request
                print(f"  → Login request to: {request.url}")
                print(f"  → Method: {request.method}")
                try:
                    print(f"  → Body: {request.post_data}")
                except:
                    pass
        
        def handle_login_response(response):
            nonlocal login_response
            if "/api/auth/login" in response.url:
                login_response = response
                print(f"  ← Login response status: {response.status}")
                try:
                    body = response.text()
                    print(f"  ← Login response body: {body[:500]}")
                except:
                    pass
        
        page.on("request", handle_login_request)
        page.on("response", handle_login_response)
        
        print("\nStep 13: Submit login form...")
        
        # Wait for the login response explicitly
        with page.expect_response(lambda response: "/api/auth/login" in response.url) as response_info:
            page.click("#login-email-form button[type='submit']")
            print("  ✓ Clicked login button")
        
        login_response = response_info.value
        print(f"\n  ← Login response received!")
        print(f"  ← Status: {login_response.status}")
        print(f"  ← Status text: {login_response.status_text}")
        
        try:
            response_body = login_response.text()
            print(f"  ← Response body: {response_body[:500]}")
        except Exception as e:
            print(f"  ⚠️ Could not read response body: {e}")
        
        # Wait a bit for page to update
        page.wait_for_timeout(2000)
        
        # Take screenshot after login
        page.screenshot(path="test-results/06-after-login.png")
        print("  ✓ Screenshot: 06-after-login.png")
        
        print("\nStep 14: Check login result...")
        print(f"  Login form visible: {page.locator('#login-form').is_visible()}")
        print(f"  Board select visible: {page.locator('#board-select').is_visible()}")
        print(f"  Main app visible: {page.locator('#main-app').is_visible()}")
        
        # Check for error notification
        notification = page.locator("#notification")
        if notification.is_visible():
            msg = page.locator("#notification-message").text_content()
            print(f"  ⚠️ Login notification: {msg}")
        
        if login_response:
            print(f"\n  Login response status: {login_response.status}")
            if login_response.status == 200:
                print("  ✓ Login successful!")
            else:
                print(f"  ✗ Login failed with status {login_response.status}")
        
        if page.locator("#board-select").is_visible():
            print("\n✅ SUCCESS! User registered and logged in!")
        else:
            print("\n❌ FAILED! Login did not succeed")
    
    print(f"\n{'='*60}")
    print("All screenshots saved to test-results/")
    print(f"{'='*60}\n")
    
    # Don't assert - just gather information
    assert True, "Debug test complete - check output above"
