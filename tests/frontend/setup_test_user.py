#!/usr/bin/env python3
"""
Test User Setup Script

This script creates a test user for frontend tests and saves the credentials
to a file that can be sourced by docker-compose and test scripts.

Usage:
    python setup_test_user.py [--base-url URL]
"""

import argparse
import os
import sys
import time
import requests
from pathlib import Path


def create_test_user(base_url: str) -> dict:
    """
    Create a test user via the API.
    
    Returns:
        dict: User credentials (email, password)
    """
    # Generate unique email based on timestamp
    timestamp = int(time.time())
    email = f"testuser_{timestamp}@example.com"
    password = "TestPassword123!"
    full_name = f"Test User {timestamp}"
    
    # Registration payload
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name
    }
    
    print(f"🔧 Creating test user: {email}")
    
    try:
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 201:
            print(f"✅ Test user created successfully!")
            return {
                "email": email,
                "password": password,
                "full_name": full_name
            }
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print(f"⚠️  User already exists, will use existing credentials")
            return {
                "email": email,
                "password": password,
                "full_name": full_name
            }
        else:
            print(f"❌ Failed to create user: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error connecting to API: {e}")
        return None


def verify_credentials(base_url: str, email: str, password: str) -> bool:
    """
    Verify that the credentials work by attempting to login.
    
    Returns:
        bool: True if login successful
    """
    print(f"🔍 Verifying credentials...")
    
    try:
        response = requests.post(
            f"{base_url}/api/auth/login",
            json={"username": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Credentials verified successfully!")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error verifying credentials: {e}")
        return False


def save_credentials(credentials: dict, output_dir: Path):
    """
    Save credentials to multiple formats for easy consumption.
    
    Args:
        credentials: User credentials dict
        output_dir: Directory to save credential files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Save as shell script (can be sourced)
    env_file = output_dir / "test-credentials.env"
    with open(env_file, 'w') as f:
        f.write(f"# Test user credentials - Generated {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"export TEST_USERNAME={credentials['email']}\n")
        f.write(f"export TEST_PASSWORD={credentials['password']}\n")
        f.write(f"export TEST_FULL_NAME='{credentials['full_name']}'\n")
    print(f"✅ Saved credentials to: {env_file}")
    
    # 2. Save as .env file (for docker-compose)
    dotenv_file = output_dir / ".env.test"
    with open(dotenv_file, 'w') as f:
        f.write(f"# Test user credentials - Generated {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"TEST_USERNAME={credentials['email']}\n")
        f.write(f"TEST_PASSWORD={credentials['password']}\n")
        f.write(f"TEST_FULL_NAME={credentials['full_name']}\n")
    print(f"✅ Saved credentials to: {dotenv_file}")
    
    # 3. Save as Python module (for pytest)
    py_file = output_dir / "test_credentials.py"
    with open(py_file, 'w') as f:
        f.write(f'"""Test user credentials - Generated {time.strftime("%Y-%m-%d %H:%M:%S")}"""\n\n')
        f.write(f'TEST_USERNAME = "{credentials["email"]}"\n')
        f.write(f'TEST_PASSWORD = "{credentials["password"]}"\n')
        f.write(f'TEST_FULL_NAME = "{credentials["full_name"]}"\n')
    print(f"✅ Saved credentials to: {py_file}")
    
    # 4. Save as JSON (for scripts)
    import json
    json_file = output_dir / "test-credentials.json"
    with open(json_file, 'w') as f:
        json.dump({
            "username": credentials["email"],
            "password": credentials["password"],
            "full_name": credentials["full_name"],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2)
    print(f"✅ Saved credentials to: {json_file}")


def main():
    parser = argparse.ArgumentParser(description="Setup test user for frontend tests")
    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL", "https://kanban.stormpath.dev"),
        help="Base URL of the application (default: https://kanban.stormpath.dev)"
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save credential files (default: current directory)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify credentials after creation"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎭 Frontend Test User Setup")
    print("=" * 60)
    print(f"Base URL: {args.base_url}")
    print(f"Output Dir: {args.output_dir}")
    print()
    
    # Create test user
    credentials = create_test_user(args.base_url)
    
    if not credentials:
        print("\n❌ Failed to create test user")
        sys.exit(1)
    
    # Verify credentials if requested
    if args.verify:
        if not verify_credentials(args.base_url, credentials["email"], credentials["password"]):
            print("\n❌ Credentials verification failed")
            sys.exit(1)
    
    # Save credentials
    output_dir = Path(args.output_dir)
    save_credentials(credentials, output_dir)
    
    print()
    print("=" * 60)
    print("✅ Test user setup complete!")
    print("=" * 60)
    print()
    print("📝 Usage:")
    print(f"   Source credentials: source {output_dir}/test-credentials.env")
    print(f"   Docker Compose:     docker-compose --env-file {output_dir}/.env.test up")
    print(f"   Python import:      from test_credentials import TEST_USERNAME, TEST_PASSWORD")
    print()
    print("🔑 Credentials:")
    print(f"   Email:    {credentials['email']}")
    print(f"   Password: {credentials['password']}")
    print()


if __name__ == "__main__":
    main()
