#!/usr/bin/env python3
"""
Test script for API key creation and authentication flow.

This script demonstrates:
1. User login to get JWT token
2. API key creation using JWT
3. API authentication using the created API key
4. Accessing secured documentation with API key
"""

import requests
import json
import sys

BASE_URL = "https://kanban.stormpath.dev"

def test_api_key_flow():
    """Test the complete API key flow."""
    print("🔐 Testing API Key Authentication Flow")
    print("=" * 50)
    
    # Step 1: Login to get JWT token
    print("\n1️⃣ Logging in to get JWT token...")
    
    # You would need actual credentials here
    login_data = {
        "username": "test@example.com",  # Replace with actual credentials
        "password": "testpassword"       # Replace with actual credentials
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            print("\n💡 To test this flow, you need to:")
            print("   1. Register a user account first")
            print("   2. Update the credentials in this script")
            print("   3. Run the script again")
            return False
            
        jwt_token = response.json()["access_token"]
        print(f"✅ Login successful! JWT token obtained.")
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        print("\n💡 Manual testing instructions:")
        print("   1. Go to https://kanban.stormpath.dev")
        print("   2. Register/login to get a JWT token")
        print("   3. Use the browser's developer tools to copy the token")
        print("   4. Test API key creation manually with curl:")
        print("      curl -X POST https://kanban.stormpath.dev/api/api-keys/ \\")
        print("        -H 'Authorization: Bearer YOUR_JWT_TOKEN' \\")
        print("        -H 'Content-Type: application/json' \\")
        print("        -d '{\"name\": \"Test Key\", \"scopes\": [\"docs\", \"read\"], \"expires_in_days\": 30}'")
        return False
    
    # Step 2: Create API key
    print("\n2️⃣ Creating API key with 'docs' and 'read' scopes...")
    
    api_key_data = {
        "name": "Test API Key",
        "description": "API key for testing authentication flow",
        "scopes": ["docs", "read"],
        "expires_in_days": 30
    }
    
    headers = {"Authorization": f"Bearer {jwt_token}"}
    response = requests.post(f"{BASE_URL}/api/api-keys/", json=api_key_data, headers=headers)
    
    if response.status_code != 201:
        print(f"❌ API key creation failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    api_key_response = response.json()
    api_key = api_key_response["api_key"]
    key_info = api_key_response["key_info"]
    
    print(f"✅ API key created successfully!")
    print(f"   Key ID: {key_info['id']}")
    print(f"   Name: {key_info['name']}")
    print(f"   Prefix: {key_info['key_prefix']}")
    print(f"   Scopes: {', '.join(key_info['scopes'])}")
    print(f"   Expires: {key_info['expires_at']}")
    print(f"   ⚠️  API Key: {api_key[:20]}... (truncated for security)")
    
    # Step 3: Test API key authentication
    print("\n3️⃣ Testing API key authentication...")
    
    api_headers = {"Authorization": f"Bearer {api_key}"}
    
    # Test accessing API endpoints
    response = requests.get(f"{BASE_URL}/api/groups/", headers=api_headers)
    if response.status_code == 200:
        print("✅ API key authentication successful for /api/groups/")
    else:
        print(f"❌ API key authentication failed: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Step 4: Test accessing secured documentation
    print("\n4️⃣ Testing secured documentation access...")
    
    response = requests.get(f"{BASE_URL}/docs", headers=api_headers)
    if response.status_code == 200:
        print("✅ API key successfully accessed secured documentation!")
        print("   Documentation is now accessible with API key authentication")
    else:
        print(f"❌ Documentation access failed: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Step 5: Test without authentication
    print("\n5️⃣ Verifying documentation is secured (testing without auth)...")
    
    response = requests.get(f"{BASE_URL}/docs")
    if response.status_code == 401:
        print("✅ Documentation properly secured - returns 401 without authentication")
    else:
        print(f"❌ Documentation security issue: {response.status_code}")
    
    print("\n🎉 API Key Flow Test Complete!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    test_api_key_flow()
