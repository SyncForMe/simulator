#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv

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

# Load JWT secret from backend/.env for testing
load_dotenv('/app/backend/.env')
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    print("Warning: JWT_SECRET not found in environment variables. Some tests may fail.")
    JWT_SECRET = "test_secret"

# Global variables for auth testing
auth_token = None
test_user_id = None

def test_login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    url = f"{API_URL}/auth/test-login"
    print(f"\nTesting: Test Login Endpoint (POST {url})")
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            return False
        
        if response.status_code == 200 and "access_token" in response_data:
            auth_token = response_data.get("access_token")
            user_data = response_data.get("user", {})
            test_user_id = user_data.get("id")
            print(f"Test login successful. User ID: {test_user_id}")
            print(f"JWT Token: {auth_token}")
            return True
        else:
            print("Test login failed. Some tests may not work correctly.")
            return False
    
    except Exception as e:
        print(f"Error during test login: {e}")
        return False

def test_document_bulk_delete_empty_test():
    """Test the document bulk delete empty test endpoint"""
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document bulk delete without authentication")
            return False
    
    url = f"{API_URL}/documents/bulk-empty-test"
    print(f"\nTesting: Document Bulk Delete Empty Test (DELETE {url})")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    print(f"Request Headers: {headers}")
    
    try:
        response = requests.delete(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            return False
        
        if response.status_code == 200 and "deleted_count" in response_data and response_data["deleted_count"] == 0:
            print("✅ Document bulk delete empty test works correctly")
            print("✅ Returned 200 with deleted_count=0")
            return True
        else:
            print("❌ Document bulk delete empty test failed")
            print(f"Expected: 200 with deleted_count=0")
            print(f"Actual: {response.status_code} with {response_data}")
            return False
    
    except Exception as e:
        print(f"Error during test: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT BULK DELETE EMPTY TEST ENDPOINT")
    print("="*80)
    
    # Test document bulk delete empty test
    empty_test_success = test_document_bulk_delete_empty_test()
    
    # Print summary
    print("\n" + "="*80)
    print("DOCUMENT BULK DELETE EMPTY TEST ENDPOINT ASSESSMENT")
    print("="*80)
    
    if empty_test_success:
        print("✅ Document bulk delete empty test endpoint is working correctly!")
        print("✅ Empty arrays are handled correctly (returns 200 with deleted_count=0)")
    else:
        print("❌ Document bulk delete empty test endpoint has issues:")
        print("  - Empty arrays are not handled correctly (should return 200 with deleted_count=0)")
    
    print("="*80)
    
    return empty_test_success

if __name__ == "__main__":
    main()
