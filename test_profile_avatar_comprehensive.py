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

def get_auth_token():
    """Get an authentication token using the test-login endpoint"""
    print("\n=== Getting authentication token ===")
    
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
    return token

def test_auth_me(token):
    """Test the /api/auth/me endpoint with the token"""
    print("\n=== Testing /api/auth/me endpoint ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    me_url = f"{API_URL}/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    me_response = requests.get(me_url, headers=headers)
    
    print(f"Response Status Code: {me_response.status_code}")
    
    if me_response.status_code != 200:
        print(f"❌ /api/auth/me failed with status code: {me_response.status_code}")
        print(f"Response: {me_response.text}")
        return False
    
    user_data = me_response.json()
    print(f"✅ Successfully retrieved user data:")
    print(json.dumps(user_data, indent=2))
    
    return True

def test_generate_profile_avatar(token, prompt="creative artist with glasses", name="User"):
    """Test the /api/auth/generate-profile-avatar endpoint"""
    print(f"\n=== Testing /api/auth/generate-profile-avatar endpoint ===")
    print(f"Prompt: '{prompt}'")
    print(f"Name: '{name}'")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test data
    data = {
        "prompt": prompt,
        "name": name
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
    
    if response.status_code == 200:
        print("✅ Profile avatar generation successful")
        avatar_url = response_data.get("avatar_url", "")
        if avatar_url:
            print(f"✅ Avatar URL: {avatar_url}")
        else:
            print("❌ Avatar URL is missing from response")
        return True
    else:
        print(f"❌ Profile avatar generation failed with status code: {response.status_code}")
        error_detail = response_data.get("detail", "No error details provided")
        print(f"❌ Error: {error_detail}")
        return False

def test_without_authentication():
    """Test the profile avatar endpoint without authentication"""
    print("\n=== Testing /api/auth/generate-profile-avatar without authentication ===")
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    data = {
        "prompt": "creative artist with glasses",
        "name": "User"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data)
    
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
    
    if response.status_code == 403:
        print("✅ Correctly rejected request without authentication")
        return True
    else:
        print("❌ Unexpected response for unauthenticated request")
        return False

def test_with_invalid_token():
    """Test the profile avatar endpoint with an invalid token"""
    print("\n=== Testing /api/auth/generate-profile-avatar with invalid token ===")
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    headers = {"Authorization": f"Bearer {invalid_token}"}
    
    data = {
        "prompt": "creative artist with glasses",
        "name": "User"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: Authorization: Bearer {invalid_token[:20]}...")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
    
    if response.status_code == 401:
        print("✅ Correctly rejected request with invalid token")
        return True
    else:
        print("❌ Unexpected response for request with invalid token")
        return False

def test_with_empty_prompt(token):
    """Test the profile avatar endpoint with an empty prompt"""
    print("\n=== Testing /api/auth/generate-profile-avatar with empty prompt ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "prompt": "",
        "name": "User"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: Authorization: Bearer {token[:20]}...")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
        return False
    
    if response.status_code == 200:
        print("✅ Successfully handled empty prompt (should use default prompt)")
        return True
    else:
        print("❌ Failed to handle empty prompt")
        return False

def test_with_missing_prompt(token):
    """Test the profile avatar endpoint with a missing prompt field"""
    print("\n=== Testing /api/auth/generate-profile-avatar with missing prompt field ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "name": "User"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: Authorization: Bearer {token[:20]}...")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
        return False
    
    if response.status_code == 200:
        print("✅ Successfully handled missing prompt (should use default prompt)")
        return True
    else:
        print("❌ Failed to handle missing prompt")
        return False

def test_with_missing_name(token):
    """Test the profile avatar endpoint with a missing name field"""
    print("\n=== Testing /api/auth/generate-profile-avatar with missing name field ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "prompt": "creative artist with glasses"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: Authorization: Bearer {token[:20]}...")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    response = requests.post(url, json=data, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
        return False
    
    if response.status_code == 200:
        print("✅ Successfully handled missing name (should use default name)")
        return True
    else:
        print("❌ Failed to handle missing name")
        return False

def test_with_malformed_request(token):
    """Test the profile avatar endpoint with a malformed request"""
    print("\n=== Testing /api/auth/generate-profile-avatar with malformed request ===")
    
    if not token:
        print("❌ Cannot test without a valid token")
        return False
    
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Send a string instead of a JSON object
    data = "This is not a JSON object"
    
    print(f"Request URL: {url}")
    print(f"Request Headers: Authorization: Bearer {token[:20]}...")
    print(f"Request Data: {data}")
    
    response = requests.post(url, data=data, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    
    try:
        response_data = response.json()
        print(f"Response Data: {json.dumps(response_data, indent=2)}")
    except json.JSONDecodeError:
        print(f"Response is not JSON: {response.text}")
        return False
    
    # We expect a 422 Unprocessable Entity or similar error
    if response.status_code >= 400:
        print("✅ Correctly rejected malformed request")
        return True
    else:
        print("❌ Unexpectedly accepted malformed request")
        return False

def run_all_tests():
    """Run all tests and print a summary"""
    print("\n=== Running all tests for /api/auth/generate-profile-avatar endpoint ===")
    
    # Get authentication token
    token = get_auth_token()
    
    # Track test results
    test_results = {}
    
    # Test authentication
    test_results["Authentication"] = test_auth_me(token)
    
    # Test profile avatar generation with valid data
    test_results["Profile Avatar Generation"] = test_generate_profile_avatar(token)
    
    # Test with empty prompt
    test_results["Empty Prompt"] = test_with_empty_prompt(token)
    
    # Test with missing prompt
    test_results["Missing Prompt"] = test_with_missing_prompt(token)
    
    # Test with missing name
    test_results["Missing Name"] = test_with_missing_name(token)
    
    # Test with malformed request
    test_results["Malformed Request"] = test_with_malformed_request(token)
    
    # Test without authentication
    test_results["Without Authentication"] = test_without_authentication()
    
    # Test with invalid token
    test_results["Invalid Token"] = test_with_invalid_token()
    
    # Print summary
    print("\n=== Test Summary ===")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    # Overall result
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"\nPassed {passed_tests} out of {total_tests} tests")
    
    if passed_tests == total_tests:
        print("✅ All tests passed! The profile avatar generation endpoint is working correctly.")
    else:
        print("❌ Some tests failed. The profile avatar generation endpoint has issues.")

if __name__ == "__main__":
    run_all_tests()