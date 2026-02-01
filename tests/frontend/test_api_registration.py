"""
Test user registration via API to verify it works
"""

import requests
import time


def test_api_registration():
    """Test registration via API to verify backend works."""
    base_url = "https://kanban.stormpath.dev"

    timestamp = int(time.time())
    user_data = {
        "username": f"apitest_{timestamp}",
        "email": f"apitest_{timestamp}@example.com",
        "password": "TestPassword123!",
        "full_name": f"API Test User {timestamp}",
    }

    print(f"\n=== Testing API Registration ===")
    print(f"Email: {user_data['email']}")
    print(f"Password: {user_data['password']}")

    # Register user
    response = requests.post(
        f"{base_url}/api/auth/register",
        json=user_data,
        verify=False,  # For self-signed certs
    )

    print(f"Registration status: {response.status_code}")
    print(f"Registration response: {response.text[:200]}")

    assert response.status_code == 201, f"Registration failed: {response.text}"

    # Try to login
    login_data = {
        "username": user_data["email"],  # Try email as username
        "password": user_data["password"],
    }

    response = requests.post(
        f"{base_url}/api/auth/login", json=login_data, verify=False
    )

    print(f"Login status: {response.status_code}")
    print(f"Login response: {response.text[:200]}")

    if response.status_code != 200:
        # Try with username field instead
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"],
        }

        response = requests.post(
            f"{base_url}/api/auth/login", json=login_data, verify=False
        )

        print(f"Login with username status: {response.status_code}")
        print(f"Login with username response: {response.text[:200]}")

    assert response.status_code == 200, f"Login failed: {response.text}"

    # Check token
    data = response.json()
    assert "access_token" in data, "No access token in response"

    print(f"✅ API registration and login successful!")
    print(f"Token: {data['access_token'][:50]}...")
