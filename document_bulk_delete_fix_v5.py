#!/usr/bin/env python3
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables from frontend/.env
load_dotenv('/app/frontend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    print("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

def login():
    """Login with test endpoint to get auth token"""
    url = f"{API_URL}/auth/test-login"
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access_token")
            user_data = data.get("user", {})
            test_user_id = user_data.get("id")
            
            print(f"Login successful. User ID: {test_user_id}")
            print(f"JWT Token: {auth_token}")
            return auth_token
        else:
            print(f"Login failed: {response.text}")
            return None
    except Exception as e:
        print(f"Error during login: {e}")
        return None

def test_document_bulk_delete_test_endpoint(auth_token):
    """Test the special test endpoint for document bulk delete with empty array"""
    url = f"{API_URL}/documents/bulk-test-empty"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }
    
    print("\nTesting document bulk delete test endpoint:")
    try:
        print(f"Request URL: {url}")
        print(f"Request Headers: {headers}")
        
        # Send the request
        response = requests.delete(url, headers=headers)
        
        # Print the response details
        print(f"Response Status Code: {response.status_code}")
        try:
            response_json = response.json()
            print(f"Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            deleted_count = data.get("deleted_count", -1)
            if deleted_count == 0:
                print("✅ Success! Test endpoint is working correctly")
                return True
            else:
                print(f"❌ Expected deleted_count=0, but got {deleted_count}")
                return False
        else:
            print(f"❌ Expected status code 200, but got {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing document bulk delete test endpoint: {e}")
        return False

def main():
    """Main function"""
    print("="*80)
    print("TESTING DOCUMENT BULK DELETE TEST ENDPOINT")
    print("="*80)
    
    # Login first
    auth_token = login()
    if not auth_token:
        print("Login failed. Cannot proceed with testing.")
        return
    
    # Test document bulk delete test endpoint
    success = test_document_bulk_delete_test_endpoint(auth_token)
    
    print("\n" + "="*80)
    if success:
        print("✅ DOCUMENT BULK DELETE TEST ENDPOINT IS WORKING CORRECTLY")
        print("This confirms that the issue is with how FastAPI is handling the request body")
        print("for the document bulk delete endpoint, not with the empty array check itself.")
    else:
        print("❌ DOCUMENT BULK DELETE TEST ENDPOINT IS NOT WORKING CORRECTLY")
    print("="*80)

if __name__ == "__main__":
    main()
