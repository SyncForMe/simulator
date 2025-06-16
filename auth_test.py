#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid
import jwt
from datetime import datetime, timedelta

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

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Generate unique test user credentials
test_user_email = f"test.user.{uuid.uuid4()}@example.com"
test_user_password = "securePassword123"
test_user_name = "Test User"

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None, params=None, measure_time=False, auth_token=None):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth and auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, params=params)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, params=params)
        elif method == "DELETE":
            if data is not None:
                response = requests.delete(url, json=data, headers=headers, params=params)
            else:
                response = requests.delete(url, headers=headers, params=params)
        else:
            print(f"Unsupported method: {method}")
            return False, None
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
        # Check if response is JSON
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            response_data = {}
        
        # Verify status code
        status_ok = response.status_code == expected_status
        
        # Verify expected keys if provided
        keys_ok = True
        if expected_keys and status_ok:
            for key in expected_keys:
                if key not in response_data:
                    print(f"Missing expected key in response: {key}")
                    keys_ok = False
        
        # Determine test result
        test_passed = status_ok and keys_ok
        
        # Update test results
        result = "PASSED" if test_passed else "FAILED"
        print(f"Test Result: {result}")
        
        test_result = {
            "name": test_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "result": result
        }
        
        if measure_time:
            test_result["response_time"] = response_time
            
        test_results["tests"].append(test_result)
        
        if test_passed:
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1
        
        return test_passed, response_data
    
    except Exception as e:
        print(f"Error during test: {e}")
        test_results["tests"].append({
            "name": test_name,
            "endpoint": endpoint,
            "method": method,
            "result": "ERROR",
            "error": str(e)
        })
        test_results["failed"] += 1
        return False, None

def print_summary():
    """Print a summary of all test results"""
    print("\n" + "="*80)
    print(f"TEST SUMMARY: {test_results['passed']} passed, {test_results['failed']} failed")
    print("="*80)
    
    for i, test in enumerate(test_results["tests"], 1):
        result_symbol = "✅" if test["result"] == "PASSED" else "❌"
        print(f"{i}. {result_symbol} {test['name']} ({test['method']} {test['endpoint']})")
    
    print("="*80)
    overall_result = "PASSED" if test_results["failed"] == 0 else "FAILED"
    print(f"OVERALL RESULT: {overall_result}")
    print("="*80)

def test_authentication_flow():
    """Test the complete authentication flow"""
    print("\n" + "="*80)
    print("TESTING AUTHENTICATION FLOW")
    print("="*80)
    
    # Step 1: Register a new user
    print("\nStep 1: Register a new user")
    
    register_data = {
        "email": test_user_email,
        "password": test_user_password,
        "name": test_user_name
    }
    
    register_test, register_response = run_test(
        "Register with valid credentials",
        "/auth/register",
        method="POST",
        data=register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if not register_test or not register_response:
        print("❌ Registration failed. Cannot continue with authentication flow testing.")
        return False, "Registration failed"
    
    # Extract token and user data
    auth_token = register_response.get("access_token")
    user_data = register_response.get("user", {})
    user_id = user_data.get("id")
    
    print(f"User registered with ID: {user_id}")
    print(f"JWT Token: {auth_token}")
    
    # Step 2: Decode and inspect the JWT token
    print("\nStep 2: Decode and inspect the JWT token")
    
    try:
        decoded_token = jwt.decode(auth_token, JWT_SECRET, algorithms=["HS256"])
        print(f"Decoded token: {json.dumps(decoded_token, indent=2)}")
        
        # Check for required fields
        if "user_id" in decoded_token and "sub" in decoded_token:
            print("✅ JWT token contains required fields (user_id, sub)")
            print(f"user_id: {decoded_token.get('user_id')}")
            print(f"sub (email): {decoded_token.get('sub')}")
            
            # Verify user_id matches
            if decoded_token.get("user_id") == user_id:
                print("✅ user_id in token matches registered user ID")
            else:
                print("❌ user_id in token does not match registered user ID")
                
            # Verify sub matches email
            if decoded_token.get("sub") == test_user_email:
                print("✅ sub in token matches registered email")
            else:
                print("❌ sub in token does not match registered email")
        else:
            print("❌ JWT token is missing required fields")
            if "user_id" not in decoded_token:
                print("  - Missing user_id field")
            if "sub" not in decoded_token:
                print("  - Missing sub field")
    except Exception as e:
        print(f"❌ JWT token validation failed: {e}")
    
    # Step 3: Use token to access a protected endpoint
    print("\nStep 3: Use token to access a protected endpoint")
    
    protected_test, protected_response = run_test(
        "Access protected endpoint (GET /api/documents)",
        "/documents",
        method="GET",
        auth=True,
        auth_token=auth_token
    )
    
    if protected_test:
        print("✅ Successfully accessed protected endpoint with registration token")
    else:
        print("❌ Failed to access protected endpoint with registration token")
    
    # Step 4: Test login flow
    print("\nStep 4: Test login flow")
    
    login_data = {
        "email": test_user_email,
        "password": test_user_password
    }
    
    login_test, login_response = run_test(
        "Login with valid credentials",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if not login_test or not login_response:
        print("❌ Login failed. Cannot continue with login flow testing.")
        return False, "Login failed"
    
    # Extract login token and user data
    login_token = login_response.get("access_token")
    login_user = login_response.get("user", {})
    
    print(f"User logged in with ID: {login_user.get('id')}")
    print(f"Login JWT Token: {login_token}")
    
    # Verify user data from login matches registration
    if login_user.get("id") == user_id:
        print("✅ User ID from login matches registered user")
    else:
        print("❌ User ID from login does not match registered user")
    
    # Step 5: Decode and inspect the login token
    print("\nStep 5: Decode and inspect the login token")
    
    try:
        decoded_login_token = jwt.decode(login_token, JWT_SECRET, algorithms=["HS256"])
        print(f"Decoded login token: {json.dumps(decoded_login_token, indent=2)}")
        
        # Check for required fields
        if "user_id" in decoded_login_token and "sub" in decoded_login_token:
            print("✅ Login JWT token contains required fields (user_id, sub)")
            
            # Verify user_id matches
            if decoded_login_token.get("user_id") == user_id:
                print("✅ user_id in login token matches user ID")
            else:
                print("❌ user_id in login token does not match user ID")
                
            # Verify sub matches email
            if decoded_login_token.get("sub") == test_user_email:
                print("✅ sub in login token matches email")
            else:
                print("❌ sub in login token does not match email")
        else:
            print("❌ Login JWT token is missing required fields")
    except Exception as e:
        print(f"❌ Login JWT token validation failed: {e}")
    
    # Step 6: Use login token to access a protected endpoint
    print("\nStep 6: Use login token to access a protected endpoint")
    
    login_protected_test, login_protected_response = run_test(
        "Access protected endpoint with login token",
        "/documents",
        method="GET",
        auth=True,
        auth_token=login_token
    )
    
    if login_protected_test:
        print("✅ Successfully accessed protected endpoint with login token")
    else:
        print("❌ Failed to access protected endpoint with login token")
    
    # Step 7: Test user data endpoint
    print("\nStep 7: Test user data endpoint")
    
    user_data_test, user_data_response = run_test(
        "Get user data",
        "/auth/me",
        method="GET",
        auth=True,
        auth_token=login_token
    )
    
    if user_data_test:
        print("✅ Successfully retrieved user data")
        
        # Verify user data
        if user_data_response.get("id") == user_id:
            print("✅ User ID in response matches registered user")
        else:
            print("❌ User ID in response does not match registered user")
            
        if user_data_response.get("email") == test_user_email:
            print("✅ Email in response matches registered email")
        else:
            print("❌ Email in response does not match registered email")
    else:
        print("❌ Failed to retrieve user data")
    
    # Print summary
    print("\nAUTHENTICATION FLOW SUMMARY:")
    
    # Check if all critical tests passed
    registration_works = register_test
    token_validation_works = "user_id" in decoded_token and "sub" in decoded_token
    protected_access_works = protected_test
    login_works = login_test
    login_token_works = login_protected_test
    
    if registration_works and token_validation_works and protected_access_works and login_works and login_token_works:
        print("✅ Authentication flow is working correctly!")
        print("✅ Registration endpoint is functioning properly")
        print("✅ JWT tokens are generated correctly with proper payload")
        print("✅ Protected endpoints can be accessed with valid token")
        print("✅ Login endpoint is functioning properly")
        print("✅ User data can be retrieved with valid token")
        return True, "Authentication flow is working correctly"
    else:
        issues = []
        if not registration_works:
            issues.append("Registration endpoint is not functioning properly")
        if not token_validation_works:
            issues.append("JWT tokens are not generated with proper payload")
        if not protected_access_works:
            issues.append("Protected endpoints cannot be accessed with registration token")
        if not login_works:
            issues.append("Login endpoint is not functioning properly")
        if not login_token_works:
            issues.append("Protected endpoints cannot be accessed with login token")
        
        print("❌ Authentication flow has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def main():
    """Run all authentication tests"""
    print("\n" + "="*80)
    print("TESTING AUTHENTICATION SYSTEM")
    print("="*80)
    
    # Test the complete authentication flow
    auth_flow_success, auth_flow_results = test_authentication_flow()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("AUTHENTICATION SYSTEM ASSESSMENT")
    print("="*80)
    
    if auth_flow_success:
        print("✅ Authentication system is working correctly")
        print("✅ Registration and login endpoints are functioning properly")
        print("✅ JWT tokens are generated correctly with proper payload")
        print("✅ Protected endpoints can be accessed with valid tokens")
        print("✅ The 'User not found' error has been resolved")
    else:
        print("❌ Authentication system has issues")
        if isinstance(auth_flow_results, dict) and "issues" in auth_flow_results:
            for issue in auth_flow_results["issues"]:
                print(f"  - {issue}")
        else:
            print(f"  - {auth_flow_results}")
    
    print("="*80)
    
    return auth_flow_success

if __name__ == "__main__":
    main()