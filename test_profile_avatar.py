#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv
import sys

# Load environment variables from frontend/.env
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

def test_auth_me():
    """Test the /api/auth/me endpoint to get a valid token"""
    print("\n=== Testing /api/auth/me endpoint ===")
    
    # First, we need to get a token using the test-login endpoint
    login_url = f"{API_URL}/auth/test-login"
    login_response = requests.post(login_url)
    
    if login_response.status_code != 200:
        print(f"❌ Test login failed with status code: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return None
    
    login_data = login_response.json()
    token = login_data.get("access_token")
    
    if not token:
        print("❌ No token received from test login")
        return None
    
    print(f"✅ Successfully obtained token: {token[:20]}...")
    
    # Now test the /api/auth/me endpoint with the token
    me_url = f"{API_URL}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = requests.get(me_url, headers=headers)
    
    if me_response.status_code != 200:
        print(f"❌ /api/auth/me failed with status code: {me_response.status_code}")
        print(f"Response: {me_response.text}")
        return None
    
    user_data = me_response.json()
    print(f"✅ Successfully retrieved user data:")
    print(json.dumps(user_data, indent=2))
    
    return token

def test_generate_profile_avatar(token):
    """Test the /api/auth/generate-profile-avatar endpoint"""
    print("\n=== Testing /api/auth/generate-profile-avatar endpoint ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test data
    data = {
        "prompt": "creative artist with glasses",
        "name": "Test User"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    # Make the request and capture detailed information
    try:
        response = requests.post(url, json=data, headers=headers)
        
        print(f"Response Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
        
        if response.status_code == 200:
            print("✅ Profile avatar generation successful")
            if response_data and "avatar_url" in response_data:
                print(f"Avatar URL: {response_data['avatar_url']}")
                # Try to access the avatar URL to verify it's valid
                avatar_response = requests.head(response_data['avatar_url'])
                print(f"Avatar URL status code: {avatar_response.status_code}")
                if avatar_response.status_code == 200:
                    print("✅ Avatar URL is valid and accessible")
                else:
                    print("⚠️ Avatar URL returned non-200 status code")
            return True
        else:
            print(f"❌ Profile avatar generation failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Exception during request: {str(e)}")
        return False

if __name__ == "__main__":
    # Test authentication first
    token = test_auth_me()
    
    # Then test profile avatar generation
    if token:
        test_generate_profile_avatar(token)
    else:
        print("❌ Cannot test profile avatar generation without a valid token")