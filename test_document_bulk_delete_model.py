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

def test_document_bulk_delete_model_empty():
    """Test the document bulk delete model endpoint with an empty array"""
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document bulk delete without authentication")
            return False
    
    url = f"{API_URL}/documents/bulk-model"
    print(f"\nTesting: Document Bulk Delete Model with Empty Array (DELETE {url})")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    data = {"document_ids": []}  # Empty array
    
    print(f"Request Headers: {headers}")
    print(f"Request Body: {data}")
    
    try:
        response = requests.delete(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            return False
        
        if response.status_code == 200 and "deleted_count" in response_data and response_data["deleted_count"] == 0:
            print("✅ Document bulk delete model with empty array works correctly")
            print("✅ Returned 200 with deleted_count=0")
            return True
        else:
            print("❌ Document bulk delete model with empty array failed")
            print(f"Expected: 200 with deleted_count=0")
            print(f"Actual: {response.status_code} with {response_data}")
            return False
    
    except Exception as e:
        print(f"Error during test: {e}")
        return False

def test_document_bulk_delete_model_nonexistent_ids():
    """Test the document bulk delete model endpoint with non-existent IDs"""
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document bulk delete without authentication")
            return False
    
    url = f"{API_URL}/documents/bulk-model"
    print(f"\nTesting: Document Bulk Delete Model with Non-Existent IDs (DELETE {url})")
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    data = {"document_ids": ["non-existent-id-1", "non-existent-id-2"]}  # Non-existent IDs
    
    print(f"Request Headers: {headers}")
    print(f"Request Body: {data}")
    
    try:
        response = requests.delete(url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            return False
        
        if response.status_code == 404:
            print("✅ Document bulk delete model with non-existent IDs works correctly")
            print("✅ Returned 404 for non-existent IDs")
            return True
        else:
            print("❌ Document bulk delete model with non-existent IDs failed")
            print(f"Expected: 404")
            print(f"Actual: {response.status_code} with {response_data}")
            return False
    
    except Exception as e:
        print(f"Error during test: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT BULK DELETE MODEL ENDPOINT")
    print("="*80)
    
    # Test document bulk delete model with empty array
    empty_array_success = test_document_bulk_delete_model_empty()
    
    # Test document bulk delete model with non-existent IDs
    nonexistent_ids_success = test_document_bulk_delete_model_nonexistent_ids()
    
    # Print summary
    print("\n" + "="*80)
    print("DOCUMENT BULK DELETE MODEL ENDPOINT ASSESSMENT")
    print("="*80)
    
    if empty_array_success and nonexistent_ids_success:
        print("✅ Document bulk delete model endpoint is working correctly!")
        print("✅ Empty arrays are handled correctly (returns 200 with deleted_count=0)")
        print("✅ Non-existent IDs are handled correctly (returns 404)")
    else:
        print("❌ Document bulk delete model endpoint has issues:")
        if not empty_array_success:
            print("  - Empty arrays are not handled correctly (should return 200 with deleted_count=0)")
        if not nonexistent_ids_success:
            print("  - Non-existent IDs are not handled correctly (should return 404)")
    
    print("="*80)
    
    return empty_array_success and nonexistent_ids_success

if __name__ == "__main__":
    main()
