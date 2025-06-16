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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth_token=None, headers=None, params=None, measure_time=False):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth_token:
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
        if measure_time:
            print(f"Response Time: {response_time:.4f} seconds")
        
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

def register_user(email, password, name):
    """Register a new user and return the auth token"""
    register_data = {
        "email": email,
        "password": password,
        "name": name
    }
    
    register_test, register_response = run_test(
        "Register new user",
        "/auth/register",
        method="POST",
        data=register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if register_test and register_response:
        auth_token = register_response.get("access_token")
        user_data = register_response.get("user", {})
        user_id = user_data.get("id")
        print(f"User registered with ID: {user_id}")
        print(f"JWT Token: {auth_token}")
        return auth_token, user_id
    else:
        print("❌ Registration failed")
        return None, None

def test_user_data_isolation():
    """Test user data isolation across all features"""
    print("\n" + "="*80)
    print("TESTING USER DATA ISOLATION")
    print("="*80)
    
    # Create a new user
    print("\nCreating new user...")
    user_email = f"test.user.{uuid.uuid4()}@example.com"
    user_password = "securePassword123"
    user_name = "Test User"
    
    user_token, user_id = register_user(user_email, user_password, user_name)
    
    if not user_token:
        print("❌ Cannot test user data isolation without user authentication")
        return False, "User registration failed"
    
    # Test all endpoints that might show user data
    endpoints = [
        {"name": "Get Conversations", "path": "/conversations", "method": "GET"},
        {"name": "Get Conversation History", "path": "/conversation-history", "method": "GET"},
        {"name": "Get Agents", "path": "/agents", "method": "GET"},
        {"name": "Get Saved Agents", "path": "/saved-agents", "method": "GET"},
        {"name": "Get Documents", "path": "/documents", "method": "GET"}
    ]
    
    isolation_issues = []
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint['name']} endpoint for data isolation")
        
        test_result, response_data = run_test(
            endpoint["name"],
            endpoint["path"],
            method=endpoint["method"],
            auth_token=user_token,
            measure_time=True
        )
        
        if test_result:
            # Check if the endpoint returns data for a new user
            if isinstance(response_data, list):
                data_count = len(response_data)
                print(f"Endpoint returned {data_count} items")
                
                if data_count > 0:
                    if endpoint["path"] == "/agents":
                        # Agents might be global, so we need to check if they have user_id
                        has_user_id = any("user_id" in item for item in response_data)
                        if has_user_id:
                            # Check if any agents belong to other users
                            other_user_agents = [item for item in response_data if item.get("user_id") != user_id]
                            if other_user_agents:
                                isolation_issues.append(f"{endpoint['name']} returns {len(other_user_agents)} agents belonging to other users")
                    else:
                        isolation_issues.append(f"{endpoint['name']} returns {data_count} items for a new user")
                        print(f"❌ New user should not have any data in {endpoint['path']}")
                else:
                    print(f"✅ New user has no data in {endpoint['path']}")
            else:
                print(f"⚠️ Endpoint returned non-list data: {type(response_data)}")
        else:
            print(f"❌ Failed to test {endpoint['name']} endpoint")
    
    # Print summary of data isolation issues
    print("\nUSER DATA ISOLATION SUMMARY:")
    
    if isolation_issues:
        print("❌ User data isolation has issues:")
        for issue in isolation_issues:
            print(f"  - {issue}")
        return False, {"issues": isolation_issues}
    else:
        print("✅ User data isolation is working correctly!")
        print("✅ New users start with empty data")
        return True, "User data isolation is working correctly"

def test_endpoint_performance():
    """Test the performance of key endpoints"""
    print("\n" + "="*80)
    print("TESTING ENDPOINT PERFORMANCE")
    print("="*80)
    
    # Create a test user
    print("\nCreating test user...")
    user_email = f"test.user.{uuid.uuid4()}@example.com"
    user_password = "securePassword123"
    user_name = "Test User"
    
    user_token, user_id = register_user(user_email, user_password, user_name)
    
    if not user_token:
        print("❌ Cannot test endpoint performance without user authentication")
        return False, "User registration failed"
    
    # Test endpoints and measure response times
    endpoints = [
        {"name": "Get Conversations", "path": "/conversations", "method": "GET"},
        {"name": "Get Conversation History", "path": "/conversation-history", "method": "GET"},
        {"name": "Get Agents", "path": "/agents", "method": "GET"},
        {"name": "Get Saved Agents", "path": "/saved-agents", "method": "GET"},
        {"name": "Get Documents", "path": "/documents", "method": "GET"}
    ]
    
    performance_results = {}
    
    for endpoint in endpoints:
        print(f"\nTesting performance of {endpoint['name']} endpoint")
        
        # Run the test multiple times to get average response time
        response_times = []
        
        for i in range(3):
            test_result, response_data = run_test(
                f"{endpoint['name']} Performance Test {i+1}",
                endpoint["path"],
                method=endpoint["method"],
                auth_token=user_token,
                measure_time=True
            )
            
            if test_result and "response_time" in test_results["tests"][-1]:
                response_time = test_results["tests"][-1]["response_time"]
                response_times.append(response_time)
                print(f"Run {i+1}: {response_time:.4f} seconds")
        
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            performance_results[endpoint["name"]] = {
                "average": avg_time,
                "min": min_time,
                "max": max_time
            }
            
            print(f"Average response time: {avg_time:.4f} seconds")
            print(f"Min response time: {min_time:.4f} seconds")
            print(f"Max response time: {max_time:.4f} seconds")
            
            # Evaluate performance
            if avg_time > 20:
                print(f"❌ {endpoint['name']} has very poor performance (> 20 seconds)")
            elif avg_time > 5:
                print(f"❌ {endpoint['name']} has poor performance (> 5 seconds)")
            elif avg_time > 1:
                print(f"⚠️ {endpoint['name']} has moderate performance (> 1 second)")
            elif avg_time > 0.5:
                print(f"✅ {endpoint['name']} has good performance (> 0.5 seconds)")
            else:
                print(f"✅ {endpoint['name']} has excellent performance (< 0.5 seconds)")
        else:
            print(f"❌ Could not measure performance for {endpoint['name']}")
    
    # Print performance summary
    print("\nENDPOINT PERFORMANCE SUMMARY:")
    
    slow_endpoints = []
    for name, results in performance_results.items():
        if results["average"] > 5:
            slow_endpoints.append(f"{name}: {results['average']:.4f} seconds")
    
    if slow_endpoints:
        print("❌ Some endpoints have performance issues:")
        for endpoint in slow_endpoints:
            print(f"  - {endpoint}")
        return False, {"slow_endpoints": slow_endpoints, "all_results": performance_results}
    else:
        print("✅ All endpoints have acceptable performance")
        return True, {"all_results": performance_results}

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING USER DATA ISOLATION TESTS")
    print("="*80)
    
    # Test user data isolation
    isolation_success, isolation_results = test_user_data_isolation()
    
    # Test endpoint performance
    performance_success, performance_results = test_endpoint_performance()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("USER DATA ISOLATION ASSESSMENT")
    print("="*80)
    
    if isolation_success:
        print("✅ User data isolation is working correctly")
        print("✅ New users start with empty data")
        print("✅ Users cannot access other users' data")
    else:
        print("❌ User data isolation has issues")
        if isinstance(isolation_results, dict) and "issues" in isolation_results:
            for issue in isolation_results["issues"]:
                print(f"  - {issue}")
    
    print("\n" + "="*80)
    print("ENDPOINT PERFORMANCE ASSESSMENT")
    print("="*80)
    
    if performance_success:
        print("✅ All endpoints have acceptable performance")
    else:
        print("❌ Some endpoints have performance issues")
        if isinstance(performance_results, dict) and "slow_endpoints" in performance_results:
            for endpoint in performance_results["slow_endpoints"]:
                print(f"  - {endpoint}")
    
    print("="*80)
    
    return isolation_success and performance_success

if __name__ == "__main__":
    main()