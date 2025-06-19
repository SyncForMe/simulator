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

def test_generate_profile_avatar(token, prompt="creative artist with glasses", name="User"):
    """Test the /api/auth/generate-profile-avatar endpoint"""
    print(f"\n=== Testing /api/auth/generate-profile-avatar endpoint with prompt='{prompt}' ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False, None
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data
    data = {
        "prompt": prompt,
        "name": name
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
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
        response_data = None
    
    if response.status_code == 200:
        print("✅ Profile avatar generation successful")
        return True, response_data
    else:
        print(f"❌ Profile avatar generation failed with status code: {response.status_code}")
        return False, response_data

def test_generate_agent_avatar(token, agent_name="Creative Artist"):
    """Test the /api/agents/generate-avatar endpoint"""
    print(f"\n=== Testing /api/agents/generate-avatar endpoint with agent_name='{agent_name}' ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False, None
    
    url = f"{API_URL}/agents/generate-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data
    data = {
        "agent_name": agent_name
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
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
        response_data = None
    
    if response.status_code == 200:
        print("✅ Agent avatar generation successful")
        return True, response_data
    else:
        print(f"❌ Agent avatar generation failed with status code: {response.status_code}")
        return False, response_data

def test_without_authentication():
    """Test both endpoints without authentication"""
    print("\n=== Testing endpoints without authentication ===")
    
    # Test profile avatar endpoint without auth
    profile_url = f"{API_URL}/auth/generate-profile-avatar"
    profile_data = {
        "prompt": "creative artist with glasses",
        "name": "User"
    }
    
    print(f"Testing {profile_url} without authentication")
    profile_response = requests.post(profile_url, json=profile_data)
    
    print(f"Response Status Code: {profile_response.status_code}")
    try:
        profile_response_data = profile_response.json()
        print(f"Response Data: {json.dumps(profile_response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {profile_response.text}")
    
    # Test agent avatar endpoint without auth
    agent_url = f"{API_URL}/agents/generate-avatar"
    agent_data = {
        "agent_name": "Creative Artist"
    }
    
    print(f"\nTesting {agent_url} without authentication")
    agent_response = requests.post(agent_url, json=agent_data)
    
    print(f"Response Status Code: {agent_response.status_code}")
    try:
        agent_response_data = agent_response.json()
        print(f"Response Data: {json.dumps(agent_response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {agent_response.text}")

def test_with_invalid_data(token):
    """Test both endpoints with invalid data"""
    print("\n=== Testing endpoints with invalid data ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test profile avatar endpoint with empty prompt
    profile_url = f"{API_URL}/auth/generate-profile-avatar"
    profile_data = {
        "prompt": "",
        "name": "User"
    }
    
    print(f"Testing {profile_url} with empty prompt")
    profile_response = requests.post(profile_url, json=profile_data, headers=headers)
    
    print(f"Response Status Code: {profile_response.status_code}")
    try:
        profile_response_data = profile_response.json()
        print(f"Response Data: {json.dumps(profile_response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {profile_response.text}")
    
    # Test agent avatar endpoint with empty agent_name
    agent_url = f"{API_URL}/agents/generate-avatar"
    agent_data = {
        "agent_name": ""
    }
    
    print(f"\nTesting {agent_url} with empty agent_name")
    agent_response = requests.post(agent_url, json=agent_data, headers=headers)
    
    print(f"Response Status Code: {agent_response.status_code}")
    try:
        agent_response_data = agent_response.json()
        print(f"Response Data: {json.dumps(agent_response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {agent_response.text}")

def test_with_invalid_token():
    """Test both endpoints with an invalid token"""
    print("\n=== Testing endpoints with invalid token ===")
    
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    # Test profile avatar endpoint with invalid token
    profile_url = f"{API_URL}/auth/generate-profile-avatar"
    profile_data = {
        "prompt": "creative artist with glasses",
        "name": "User"
    }
    
    print(f"Testing {profile_url} with invalid token")
    profile_response = requests.post(profile_url, json=profile_data, headers=headers)
    
    print(f"Response Status Code: {profile_response.status_code}")
    try:
        profile_response_data = profile_response.json()
        print(f"Response Data: {json.dumps(profile_response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {profile_response.text}")
    
    # Test agent avatar endpoint with invalid token
    agent_url = f"{API_URL}/agents/generate-avatar"
    agent_data = {
        "agent_name": "Creative Artist"
    }
    
    print(f"\nTesting {agent_url} with invalid token")
    agent_response = requests.post(agent_url, json=agent_data, headers=headers)
    
    print(f"Response Status Code: {agent_response.status_code}")
    try:
        agent_response_data = agent_response.json()
        print(f"Response Data: {json.dumps(agent_response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {agent_response.text}")

def compare_endpoints(token):
    """Compare the behavior of both endpoints with the same input"""
    print("\n=== Comparing both endpoints with the same input ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return
    
    # Test both endpoints with the same input
    prompt = "creative artist with glasses"
    name = "Creative Artist"
    
    # Test profile avatar endpoint
    profile_success, profile_data = test_generate_profile_avatar(token, prompt, name)
    
    # Test agent avatar endpoint
    agent_success, agent_data = test_generate_agent_avatar(token, name)
    
    # Compare results
    print("\n=== Comparison Results ===")
    print(f"Profile Avatar Success: {profile_success}")
    print(f"Agent Avatar Success: {agent_success}")
    
    if profile_success and agent_success:
        print("✅ Both endpoints are working correctly")
        
        # Compare response structure
        profile_keys = set(profile_data.keys())
        agent_keys = set(agent_data.keys())
        
        print(f"Profile Avatar Response Keys: {profile_keys}")
        print(f"Agent Avatar Response Keys: {agent_keys}")
        
        common_keys = profile_keys.intersection(agent_keys)
        profile_only_keys = profile_keys - agent_keys
        agent_only_keys = agent_keys - profile_keys
        
        print(f"Common Keys: {common_keys}")
        print(f"Profile-only Keys: {profile_only_keys}")
        print(f"Agent-only Keys: {agent_only_keys}")
        
        # Compare avatar URLs
        profile_url = profile_data.get("avatar_url", "")
        agent_url = agent_data.get("avatar_url", "")
        
        print(f"Profile Avatar URL: {profile_url}")
        print(f"Agent Avatar URL: {agent_url}")
        
        if profile_url and agent_url:
            print("✅ Both endpoints return valid avatar URLs")
        else:
            if not profile_url:
                print("❌ Profile avatar URL is missing")
            if not agent_url:
                print("❌ Agent avatar URL is missing")
    else:
        if not profile_success:
            print("❌ Profile avatar generation failed")
        if not agent_success:
            print("❌ Agent avatar generation failed")

if __name__ == "__main__":
    # Test authentication first
    token = test_auth_me()
    
    # Test both endpoints with valid data
    if token:
        test_generate_profile_avatar(token)
        test_generate_agent_avatar(token)
        
        # Test with invalid data
        test_with_invalid_data(token)
        
        # Compare endpoints
        compare_endpoints(token)
    else:
        print("❌ Cannot test avatar generation without a valid token")
    
    # Test without authentication
    test_without_authentication()
    
    # Test with invalid token
    test_with_invalid_token()