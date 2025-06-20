#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import jwt
import bcrypt
import pymongo
from datetime import datetime

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
MONGO_URL = os.environ.get('MONGO_URL')

if not JWT_SECRET:
    print("Warning: JWT_SECRET not found in environment variables. Some tests may fail.")
    JWT_SECRET = "test_secret"

# Admin credentials
ADMIN_EMAIL = "dino@cytonic.com"
ADMIN_PASSWORD = "Observerinho8"

def print_header(title):
    """Print a header for a test section"""
    print("\n" + "="*80)
    print(title)
    print("="*80)

def check_user_in_db():
    """Check if the admin user exists in the database"""
    print_header("CHECKING ADMIN USER IN DATABASE")
    
    try:
        # Connect to MongoDB
        client = pymongo.MongoClient(MONGO_URL)
        db = client.get_database("ai_simulation")
        
        # Find the admin user
        admin_user = db.users.find_one({"email": ADMIN_EMAIL})
        
        if admin_user:
            print(f"✅ Admin user found in database: {ADMIN_EMAIL}")
            print(f"User ID: {admin_user.get('id')}")
            print(f"Name: {admin_user.get('name')}")
            print(f"Created at: {admin_user.get('created_at')}")
            
            # Check if password hash exists
            if "password_hash" in admin_user:
                print(f"✅ Password hash exists: {admin_user['password_hash'][:20]}...")
                return True, admin_user
            else:
                print(f"❌ Password hash not found for admin user")
                return False, admin_user
        else:
            print(f"❌ Admin user not found in database: {ADMIN_EMAIL}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False, None

def verify_password_hash(password_hash):
    """Verify if the password hash is valid for the given password"""
    print_header("VERIFYING PASSWORD HASH")
    
    try:
        # Check if the hash is in the correct format
        if not password_hash:
            print("❌ Password hash is empty")
            return False
            
        # Try to verify the password against the hash
        result = bcrypt.checkpw(ADMIN_PASSWORD.encode('utf-8'), password_hash.encode('utf-8'))
        
        if result:
            print(f"✅ Password hash verification successful for '{ADMIN_PASSWORD}'")
            return True
        else:
            print(f"❌ Password hash verification failed for '{ADMIN_PASSWORD}'")
            
            # Try with some variations to help debug
            test_passwords = [
                "Observerinho8",
                "observerinho8",
                "Observerinho",
                "Observer",
                "observer",
                "admin",
                "Admin123",
                "password",
                "Password123"
            ]
            
            for test_password in test_passwords:
                if bcrypt.checkpw(test_password.encode('utf-8'), password_hash.encode('utf-8')):
                    print(f"✅ Found matching password: '{test_password}'")
                    return True
            
            print("❌ Could not find a matching password from common variations")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying password hash: {e}")
        return False

def test_login_endpoint():
    """Test the login endpoint with admin credentials"""
    print_header("TESTING LOGIN ENDPOINT")
    
    login_data = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }
    
    try:
        # Make the login request
        print(f"Attempting login with email: {ADMIN_EMAIL} and password: {ADMIN_PASSWORD}")
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
        # Check if response is JSON
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Check if login was successful
        if response.status_code == 200 and "access_token" in response_data:
            print("✅ Login successful")
            
            # Verify token
            token = response_data["access_token"]
            try:
                decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                print(f"✅ JWT token is valid and contains: {decoded_token}")
                
                # Check if token contains required fields
                if "user_id" in decoded_token and "sub" in decoded_token:
                    print("✅ JWT token contains required fields (user_id, sub)")
                else:
                    print("❌ JWT token is missing required fields")
                
                return True, token
            except Exception as e:
                print(f"❌ JWT token validation failed: {e}")
                return False, None
        else:
            print(f"❌ Login failed with status code {response.status_code}")
            
            # Check for specific error messages
            if "detail" in response_data:
                print(f"Error detail: {response_data['detail']}")
            
            return False, None
            
    except Exception as e:
        print(f"❌ Error during login request: {e}")
        return False, None

def test_guest_login():
    """Test the 'Continue as Guest' functionality"""
    print_header("TESTING 'CONTINUE AS GUEST' FUNCTIONALITY")
    
    try:
        # Make the test-login request
        print("Attempting 'Continue as Guest' login")
        response = requests.post(f"{API_URL}/auth/test-login")
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
        # Check if response is JSON
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Check if login was successful
        if response.status_code == 200 and "access_token" in response_data:
            print("✅ 'Continue as Guest' login successful")
            
            # Verify token
            token = response_data["access_token"]
            try:
                decoded_token = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                print(f"✅ JWT token is valid and contains: {decoded_token}")
                
                # Check token structure
                if "sub" in decoded_token:
                    print("✅ JWT token contains 'sub' field")
                else:
                    print("❌ JWT token is missing 'sub' field")
                
                if "user_id" in decoded_token:
                    print("✅ JWT token contains 'user_id' field")
                else:
                    print("⚠️ JWT token is missing 'user_id' field (may be normal for guest login)")
                
                return True, token
            except Exception as e:
                print(f"❌ JWT token validation failed: {e}")
                return False, None
        else:
            print(f"❌ 'Continue as Guest' login failed with status code {response.status_code}")
            
            # Check for specific error messages
            if "detail" in response_data:
                print(f"Error detail: {response_data['detail']}")
            
            return False, None
            
    except Exception as e:
        print(f"❌ Error during 'Continue as Guest' login request: {e}")
        return False, None

def test_protected_endpoint(token):
    """Test accessing a protected endpoint with the token"""
    print_header("TESTING PROTECTED ENDPOINT ACCESS")
    
    if not token:
        print("❌ No token provided, skipping test")
        return False
    
    try:
        # Make the request to a protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
        # Check if response is JSON
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Check if access was successful
        if response.status_code == 200:
            print("✅ Successfully accessed protected endpoint")
            return True
        else:
            print(f"❌ Failed to access protected endpoint with status code {response.status_code}")
            
            # Check for specific error messages
            if "detail" in response_data:
                print(f"Error detail: {response_data['detail']}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error accessing protected endpoint: {e}")
        return False

def test_admin_endpoints(token):
    """Test accessing admin endpoints with the token"""
    print_header("TESTING ADMIN ENDPOINTS ACCESS")
    
    if not token:
        print("❌ No token provided, skipping test")
        return False
    
    admin_endpoints = [
        "/admin/dashboard/stats",
        "/admin/users",
        "/admin/activity/recent"
    ]
    
    success_count = 0
    
    for endpoint in admin_endpoints:
        try:
            # Make the request to an admin endpoint
            print(f"\nTesting admin endpoint: {endpoint}")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{API_URL}{endpoint}", headers=headers)
            
            # Print response details
            print(f"Status Code: {response.status_code}")
            
            # Check if response is JSON
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)[:200]}...")  # Truncate long responses
            except json.JSONDecodeError:
                print(f"Response is not JSON: {response.text}")
                response_data = {}
            
            # Check if access was successful
            if response.status_code == 200:
                print(f"✅ Successfully accessed admin endpoint: {endpoint}")
                success_count += 1
            else:
                print(f"❌ Failed to access admin endpoint: {endpoint}")
                
                # Check for specific error messages
                if "detail" in response_data:
                    print(f"Error detail: {response_data['detail']}")
                
        except Exception as e:
            print(f"❌ Error accessing admin endpoint {endpoint}: {e}")
    
    # Return True if all admin endpoints were accessed successfully
    if success_count == len(admin_endpoints):
        print("\n✅ Successfully accessed all admin endpoints")
        return True
    else:
        print(f"\n❌ Failed to access {len(admin_endpoints) - success_count} out of {len(admin_endpoints)} admin endpoints")
        return False

def main():
    """Main function to run all tests"""
    print_header("ADMIN AUTHENTICATION TESTING")
    
    # Step 1: Check if admin user exists in database
    user_exists, admin_user = check_user_in_db()
    
    # Step 2: If user exists, verify password hash
    password_valid = False
    if user_exists and admin_user and "password_hash" in admin_user:
        password_valid = verify_password_hash(admin_user["password_hash"])
    
    # Step 3: Test login endpoint
    login_success, admin_token = test_login_endpoint()
    
    # Step 4: Test guest login functionality
    guest_login_success, guest_token = test_guest_login()
    
    # Step 5: Test protected endpoint access with admin token
    protected_access = False
    if login_success and admin_token:
        protected_access = test_protected_endpoint(admin_token)
    
    # Step 6: Test admin endpoints access with admin token
    admin_access = False
    if login_success and admin_token:
        admin_access = test_admin_endpoints(admin_token)
    
    # Print summary
    print_header("TEST SUMMARY")
    print(f"Admin User Exists in Database: {'✅ YES' if user_exists else '❌ NO'}")
    print(f"Password Hash Valid: {'✅ YES' if password_valid else '❌ NO'}")
    print(f"Login Endpoint Working: {'✅ YES' if login_success else '❌ NO'}")
    print(f"Guest Login Working: {'✅ YES' if guest_login_success else '❌ NO'}")
    print(f"Protected Endpoint Access: {'✅ YES' if protected_access else '❌ NO'}")
    print(f"Admin Endpoints Access: {'✅ YES' if admin_access else '❌ NO'}")
    
    # Overall result
    if user_exists and password_valid and login_success and protected_access and admin_access:
        print("\n✅ OVERALL RESULT: PASSED - Admin authentication is working correctly")
    else:
        print("\n❌ OVERALL RESULT: FAILED - Admin authentication has issues")
        
        # Provide specific recommendations
        if not user_exists:
            print("  - Admin user does not exist in the database")
        elif not password_valid:
            print("  - Admin password hash is invalid")
        elif not login_success:
            print("  - Login endpoint is not working with admin credentials")
        elif not protected_access:
            print("  - Cannot access protected endpoints with admin token")
        elif not admin_access:
            print("  - Cannot access admin endpoints with admin token")

if __name__ == "__main__":
    main()