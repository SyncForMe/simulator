#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import bcrypt

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

# Admin credentials
ADMIN_EMAIL = "dino@cytonic.com"
ADMIN_PASSWORD = "Observerinho8"
ADMIN_NAME = "Dino Observer"

def register_admin_user():
    """Register the admin user"""
    print("\n" + "="*80)
    print("REGISTERING ADMIN USER")
    print("="*80)
    
    register_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "name": ADMIN_NAME
    }
    
    try:
        # Make the registration request
        print(f"Attempting to register admin user: {ADMIN_EMAIL}")
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
        # Check if response is JSON
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Check if registration was successful
        if response.status_code == 200 and "access_token" in response_data:
            print("✅ Admin user registration successful")
            return True
        else:
            print(f"❌ Admin user registration failed with status code {response.status_code}")
            
            # Check for specific error messages
            if "detail" in response_data:
                print(f"Error detail: {response_data['detail']}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error during registration request: {e}")
        return False

if __name__ == "__main__":
    register_admin_user()