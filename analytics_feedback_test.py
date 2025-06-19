#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid
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

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "tests": []
}

# Global variables for auth testing
auth_token = None
test_user_id = None

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None, params=None, measure_time=False):
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

def test_login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    # Try using the email/password login first
    login_data = {
        "email": "dino@cytonic.com",
        "password": "Observerinho8"
    }
    
    login_test, login_response = run_test(
        "Login with credentials",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    # If email/password login fails, try the test login endpoint
    if not login_test or not login_response:
        test_login_test, test_login_response = run_test(
            "Test Login Endpoint",
            "/auth/test-login",
            method="POST",
            expected_keys=["access_token", "token_type", "user"]
        )
        
        # Store the token for further testing if successful
        if test_login_test and test_login_response:
            auth_token = test_login_response.get("access_token")
            user_data = test_login_response.get("user", {})
            test_user_id = user_data.get("id")
            print(f"Test login successful. User ID: {test_user_id}")
            print(f"JWT Token: {auth_token}")
            return True
        else:
            print("Test login failed. Some tests may not work correctly.")
            return False
    else:
        # Store the token from email/password login
        auth_token = login_response.get("access_token")
        user_data = login_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"Login successful. User ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        return True

def test_analytics_endpoints():
    """Test the analytics endpoints"""
    print("\n" + "="*80)
    print("TESTING ANALYTICS ENDPOINTS")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test analytics endpoints without authentication")
            return False, "Authentication failed"
    
    # Test 1: Test comprehensive analytics endpoint
    print("\nTest 1: Testing comprehensive analytics endpoint")
    
    comprehensive_test, comprehensive_response = run_test(
        "Comprehensive Analytics",
        "/analytics/comprehensive",
        method="GET",
        auth=True,
        expected_keys=["summary", "daily_activity", "agent_usage", "scenario_distribution", "api_usage", "generated_at"]
    )
    
    if comprehensive_test and comprehensive_response:
        print("✅ Comprehensive analytics endpoint is working correctly")
        
        # Verify the structure of the response
        summary = comprehensive_response.get("summary", {})
        daily_activity = comprehensive_response.get("daily_activity", [])
        agent_usage = comprehensive_response.get("agent_usage", [])
        scenario_distribution = comprehensive_response.get("scenario_distribution", [])
        api_usage = comprehensive_response.get("api_usage", {})
        
        # Check summary structure
        summary_keys = ["total_conversations", "conversations_this_week", "conversations_this_month", 
                        "total_agents", "agents_this_week", "total_documents", "documents_this_week"]
        
        missing_summary_keys = [key for key in summary_keys if key not in summary]
        if missing_summary_keys:
            print(f"❌ Missing summary keys: {', '.join(missing_summary_keys)}")
        else:
            print("✅ Summary contains all required fields")
        
        # Check daily activity structure
        if daily_activity and isinstance(daily_activity, list):
            print(f"✅ Daily activity contains {len(daily_activity)} days of data")
            if daily_activity[0]:
                print(f"✅ Daily activity format: {daily_activity[0]}")
        else:
            print("❌ Daily activity is missing or not a list")
        
        # Check agent usage structure
        if agent_usage and isinstance(agent_usage, list):
            print(f"✅ Agent usage contains {len(agent_usage)} agents")
            if agent_usage[0]:
                print(f"✅ Agent usage format: {agent_usage[0]}")
        else:
            print("❌ Agent usage is missing or not a list")
        
        # Check scenario distribution structure
        if scenario_distribution and isinstance(scenario_distribution, list):
            print(f"✅ Scenario distribution contains {len(scenario_distribution)} scenarios")
            if scenario_distribution[0]:
                print(f"✅ Scenario distribution format: {scenario_distribution[0]}")
        else:
            print("❌ Scenario distribution is missing or not a list")
        
        # Check API usage structure
        api_usage_keys = ["current_usage", "max_requests", "remaining", "history"]
        missing_api_keys = [key for key in api_usage_keys if key not in api_usage]
        if missing_api_keys:
            print(f"❌ Missing API usage keys: {', '.join(missing_api_keys)}")
        else:
            print("✅ API usage contains all required fields")
    else:
        print("❌ Comprehensive analytics endpoint is not working correctly")
    
    # Test 2: Test weekly summary endpoint
    print("\nTest 2: Testing weekly summary endpoint")
    
    weekly_test, weekly_response = run_test(
        "Weekly Summary",
        "/analytics/weekly-summary",
        method="GET",
        auth=True,
        expected_keys=["period", "conversations", "agents_created", "documents_created", 
                       "most_active_day", "daily_breakdown", "generated_at"]
    )
    
    if weekly_test and weekly_response:
        print("✅ Weekly summary endpoint is working correctly")
        
        # Verify the structure of the response
        period = weekly_response.get("period")
        conversations = weekly_response.get("conversations")
        agents_created = weekly_response.get("agents_created")
        documents_created = weekly_response.get("documents_created")
        most_active_day = weekly_response.get("most_active_day")
        daily_breakdown = weekly_response.get("daily_breakdown", {})
        
        print(f"✅ Period: {period}")
        print(f"✅ Conversations: {conversations}")
        print(f"✅ Agents created: {agents_created}")
        print(f"✅ Documents created: {documents_created}")
        print(f"✅ Most active day: {most_active_day}")
        
        # Check daily breakdown structure
        if daily_breakdown and isinstance(daily_breakdown, dict):
            print(f"✅ Daily breakdown contains {len(daily_breakdown)} days")
            print(f"✅ Daily breakdown format: {daily_breakdown}")
        else:
            print("❌ Daily breakdown is missing or not a dictionary")
    else:
        print("❌ Weekly summary endpoint is not working correctly")
    
    # Test 3: Test analytics endpoints without authentication
    print("\nTest 3: Testing analytics endpoints without authentication")
    
    # Test comprehensive analytics without auth
    no_auth_comprehensive_test, _ = run_test(
        "Comprehensive Analytics Without Auth",
        "/analytics/comprehensive",
        method="GET",
        auth=False,
        expected_status=403
    )
    
    if no_auth_comprehensive_test:
        print("✅ Comprehensive analytics endpoint correctly requires authentication")
    else:
        print("❌ Comprehensive analytics endpoint does not properly enforce authentication")
    
    # Test weekly summary without auth
    no_auth_weekly_test, _ = run_test(
        "Weekly Summary Without Auth",
        "/analytics/weekly-summary",
        method="GET",
        auth=False,
        expected_status=403
    )
    
    if no_auth_weekly_test:
        print("✅ Weekly summary endpoint correctly requires authentication")
    else:
        print("❌ Weekly summary endpoint does not properly enforce authentication")
    
    # Print summary
    print("\nANALYTICS ENDPOINTS SUMMARY:")
    
    if comprehensive_test and weekly_test and no_auth_comprehensive_test and no_auth_weekly_test:
        print("✅ All analytics endpoints are working correctly")
        print("✅ Authentication is properly enforced")
        print("✅ Response data structures match the expected schema")
        return True, "All analytics endpoints are working correctly"
    else:
        issues = []
        if not comprehensive_test:
            issues.append("Comprehensive analytics endpoint is not working correctly")
        if not weekly_test:
            issues.append("Weekly summary endpoint is not working correctly")
        if not no_auth_comprehensive_test:
            issues.append("Comprehensive analytics endpoint does not properly enforce authentication")
        if not no_auth_weekly_test:
            issues.append("Weekly summary endpoint does not properly enforce authentication")
        
        print("❌ Analytics endpoints have issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_feedback_endpoint():
    """Test the feedback endpoint"""
    print("\n" + "="*80)
    print("TESTING FEEDBACK ENDPOINT")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test feedback endpoint without authentication")
            return False, "Authentication failed"
    
    # Test 1: Send valid feedback
    print("\nTest 1: Sending valid feedback")
    
    feedback_data = {
        "subject": "Test Feedback",
        "message": "This is a test feedback message. The application is working great!",
        "type": "general"
    }
    
    feedback_test, feedback_response = run_test(
        "Send Feedback",
        "/feedback/send",
        method="POST",
        data=feedback_data,
        auth=True,
        expected_keys=["success", "message", "feedback_id"]
    )
    
    if feedback_test and feedback_response:
        print("✅ Feedback endpoint is working correctly")
        
        # Verify the structure of the response
        success = feedback_response.get("success")
        message = feedback_response.get("message")
        feedback_id = feedback_response.get("feedback_id")
        
        if success and message and feedback_id:
            print("✅ Feedback response contains all required fields")
            print(f"✅ Feedback ID: {feedback_id}")
        else:
            print("❌ Feedback response is missing required fields")
    else:
        print("❌ Feedback endpoint is not working correctly")
    
    # Test 2: Send feedback with empty message
    print("\nTest 2: Sending feedback with empty message")
    
    empty_feedback_data = {
        "subject": "Test Feedback",
        "message": "",
        "type": "general"
    }
    
    empty_feedback_test, _ = run_test(
        "Send Feedback with Empty Message",
        "/feedback/send",
        method="POST",
        data=empty_feedback_data,
        auth=True,
        expected_status=400
    )
    
    if empty_feedback_test:
        print("✅ Feedback endpoint correctly rejects empty messages")
    else:
        print("❌ Feedback endpoint does not properly validate empty messages")
    
    # Test 3: Send feedback without authentication
    print("\nTest 3: Sending feedback without authentication")
    
    no_auth_feedback_test, _ = run_test(
        "Send Feedback Without Auth",
        "/feedback/send",
        method="POST",
        data=feedback_data,
        auth=False,
        expected_status=403
    )
    
    if no_auth_feedback_test:
        print("✅ Feedback endpoint correctly requires authentication")
    else:
        print("❌ Feedback endpoint does not properly enforce authentication")
    
    # Print summary
    print("\nFEEDBACK ENDPOINT SUMMARY:")
    
    if feedback_test and empty_feedback_test and no_auth_feedback_test:
        print("✅ Feedback endpoint is working correctly")
        print("✅ Authentication is properly enforced")
        print("✅ Input validation is working correctly")
        return True, "Feedback endpoint is working correctly"
    else:
        issues = []
        if not feedback_test:
            issues.append("Feedback endpoint is not working correctly")
        if not empty_feedback_test:
            issues.append("Feedback endpoint does not properly validate empty messages")
        if not no_auth_feedback_test:
            issues.append("Feedback endpoint does not properly enforce authentication")
        
        print("❌ Feedback endpoint has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

if __name__ == "__main__":
    print("Starting analytics and feedback API tests...")
    
    # Test login first to get authentication token
    test_login()
    
    # Test analytics endpoints
    analytics_result, _ = test_analytics_endpoints()
    
    # Test feedback endpoint
    feedback_result, _ = test_feedback_endpoint()
    
    # Print overall summary
    print_summary()
    
    # Exit with appropriate status code
    if analytics_result and feedback_result:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)