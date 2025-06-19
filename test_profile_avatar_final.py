#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv
import sys
import time

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
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data as specified in the review request
    data = {
        "prompt": "creative artist with glasses",
        "name": "User"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: Authorization: Bearer {token[:20]}...")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    start_time = time.time()
    response = requests.post(url, json=data, headers=headers)
    end_time = time.time()
    
    print(f"Response Time: {end_time - start_time:.2f} seconds")
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
        return False
    
    # Check status code
    print(f"\nStatus Code Analysis:")
    if response.status_code == 200:
        print(f"✅ Status Code: {response.status_code} (Success)")
    else:
        print(f"❌ Status Code: {response.status_code} (Error)")
    
    # Check for error message
    print(f"\nError Message Analysis:")
    if response.status_code != 200:
        error_detail = response_data.get("detail", "No error details provided")
        print(f"❌ Error Message: {error_detail}")
    else:
        print(f"✅ No error message (successful response)")
    
    # Check for avatar URL
    print(f"\nResponse Data Analysis:")
    if response.status_code == 200:
        success = response_data.get("success", False)
        avatar_url = response_data.get("avatar_url", "")
        
        if success:
            print(f"✅ Success: {success}")
        else:
            print(f"❌ Success: {success}")
        
        if avatar_url:
            print(f"✅ Avatar URL: {avatar_url}")
        else:
            print(f"❌ Avatar URL is missing from response")
    
    # Check if fal.ai client is working properly
    print(f"\nFal.ai Client Analysis:")
    if response.status_code == 200 and response_data.get("avatar_url", "").startswith("https://v3.fal.media/"):
        print(f"✅ Fal.ai client is working properly (URL starts with https://v3.fal.media/)")
    else:
        print(f"❌ Fal.ai client may not be working properly")
    
    # Overall assessment
    print(f"\nOverall Assessment:")
    if response.status_code == 200 and response_data.get("success", False) and response_data.get("avatar_url", ""):
        print(f"✅ Profile avatar generation is working correctly")
        return True
    else:
        print(f"❌ Profile avatar generation is not working correctly")
        return False

if __name__ == "__main__":
    # Test authentication first
    token = test_auth_me()
    
    # Then test profile avatar generation
    if token:
        test_generate_profile_avatar(token)
    else:
        print("❌ Cannot test profile avatar generation without a valid token")