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

def test_generate_agent_avatar(token):
    """Test the /api/agents/generate-avatar endpoint"""
    print("\n=== Testing /api/agents/generate-avatar endpoint ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    url = f"{API_URL}/agents/generate-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data
    data = {
        "agent_name": "Creative Artist"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
    
    if response.status_code == 200:
        print("✅ Agent avatar generation successful")
        return True
    else:
        print(f"❌ Agent avatar generation failed with status code: {response.status_code}")
        return False

if __name__ == "__main__":
    # Test authentication first
    token = test_auth_me()
    
    # Then test agent avatar generation
    if token:
        test_generate_agent_avatar(token)
    else:
        print("❌ Cannot test agent avatar generation without a valid token")