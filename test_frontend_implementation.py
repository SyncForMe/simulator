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

def test_frontend_implementation():
    """Test the frontend implementation of the profile avatar generation"""
    print("\n=== Testing Frontend Implementation of Profile Avatar Generation ===")
    
    # Step 1: Get a token
    login_url = f"{API_URL}/auth/test-login"
    login_response = requests.post(login_url)
    
    if login_response.status_code != 200:
        print(f"❌ Test login failed with status code: {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return
    
    login_data = login_response.json()
    token = login_data.get("access_token")
    
    if not token:
        print("❌ No token received from test login")
        return
    
    print(f"✅ Successfully obtained token: {token[:20]}...")
    
    # Step 2: Test the profile avatar generation endpoint with the same parameters as the frontend
    url = f"{API_URL}/auth/generate-profile-avatar"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use the same data structure as in the frontend code
    data = {
        "prompt": "creative artist with glasses",
        "name": "User"
    }
    
    print(f"Request URL: {url}")
    print(f"Request Headers: {headers}")
    print(f"Request Data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        print(f"Response Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            return
        
        if response.status_code == 200:
            print("✅ Profile avatar generation successful")
            avatar_url = response_data.get("avatar_url")
            if avatar_url:
                print(f"✅ Avatar URL: {avatar_url}")
                
                # Check if the avatar URL is accessible
                avatar_response = requests.head(avatar_url)
                print(f"Avatar URL status code: {avatar_response.status_code}")
                
                if avatar_response.status_code == 200:
                    print("✅ Avatar URL is valid and accessible")
                else:
                    print("❌ Avatar URL is not accessible")
            else:
                print("❌ Avatar URL is missing from response")
        else:
            print(f"❌ Profile avatar generation failed with status code: {response.status_code}")
            error_detail = response_data.get("detail", "No error details provided")
            print(f"❌ Error: {error_detail}")
    except Exception as e:
        print(f"❌ Exception during request: {str(e)}")

    # Step 3: Provide recommendations for fixing the frontend code
    print("\n=== Recommendations for Frontend Fix ===")
    print("1. Uncomment the actual API call in AccountModals.js (lines 85-102)")
    print("2. Remove or comment out the simulated response (lines 72-79)")
    print("3. Uncomment the setIsGenerating(false) line in the finally block (line 107)")
    print("4. Ensure the API URL is correctly set in the frontend environment")
    print("5. Verify that the token is being properly passed in the Authorization header")

if __name__ == "__main__":
    test_frontend_implementation()