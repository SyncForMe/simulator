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

# Global variables for auth testing
auth_token = None
test_user_id = None
test_user_email = f"test.user.{uuid.uuid4()}@example.com"
test_user_password = "securePassword123"
test_user_name = "Test User"

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
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
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
    
    # Test 1: Test the comprehensive analytics endpoint
    print("\nTest 1: Testing comprehensive analytics endpoint")
    
    comprehensive_test, comprehensive_response = run_test(
        "Comprehensive Analytics",
        "/analytics/comprehensive",
        method="GET",
        auth=True,
        expected_keys=["summary", "daily_activity", "agent_usage", "scenario_distribution", "api_usage", "generated_at"]
    )
    
    if comprehensive_test and comprehensive_response:
        print("✅ Comprehensive analytics endpoint returned successfully")
        
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
        
        if not missing_summary_keys:
            print("✅ Summary contains all required fields")
        else:
            print(f"❌ Summary is missing fields: {', '.join(missing_summary_keys)}")
        
        # Check daily activity structure
        if daily_activity and isinstance(daily_activity, list) and len(daily_activity) == 30:
            print(f"✅ Daily activity contains data for 30 days")
            
            # Check structure of a sample day
            sample_day = daily_activity[0]
            if "date" in sample_day and "conversations" in sample_day:
                print("✅ Daily activity has correct structure")
            else:
                print("❌ Daily activity has incorrect structure")
        else:
            print(f"❌ Daily activity should contain 30 days of data, found {len(daily_activity)}")
        
        # Check agent usage structure
        if isinstance(agent_usage, list):
            print(f"✅ Agent usage contains {len(agent_usage)} agents")
            
            if agent_usage:
                # Check structure of a sample agent
                sample_agent = agent_usage[0]
                if "name" in sample_agent and "usage_count" in sample_agent and "archetype" in sample_agent:
                    print("✅ Agent usage has correct structure")
                else:
                    print("❌ Agent usage has incorrect structure")
        else:
            print("❌ Agent usage should be a list")
        
        # Check scenario distribution structure
        if isinstance(scenario_distribution, list):
            print(f"✅ Scenario distribution contains {len(scenario_distribution)} scenarios")
            
            if scenario_distribution:
                # Check structure of a sample scenario
                sample_scenario = scenario_distribution[0]
                if "scenario" in sample_scenario and "count" in sample_scenario:
                    print("✅ Scenario distribution has correct structure")
                else:
                    print("❌ Scenario distribution has incorrect structure")
        else:
            print("❌ Scenario distribution should be a list")
        
        # Check API usage structure
        api_usage_keys = ["current_usage", "max_requests", "remaining", "history"]
        missing_api_keys = [key for key in api_usage_keys if key not in api_usage]
        
        if not missing_api_keys:
            print("✅ API usage contains all required fields")
            
            # Check history structure
            history = api_usage.get("history", [])
            if isinstance(history, list):
                print(f"✅ API usage history contains {len(history)} entries")
                
                if history:
                    # Check structure of a sample history entry
                    sample_history = history[0]
                    if "date" in sample_history and "requests" in sample_history:
                        print("✅ API usage history has correct structure")
                    else:
                        print("❌ API usage history has incorrect structure")
            else:
                print("❌ API usage history should be a list")
        else:
            print(f"❌ API usage is missing fields: {', '.join(missing_api_keys)}")
    else:
        print("❌ Comprehensive analytics endpoint failed")
    
    # Test 2: Test the weekly summary endpoint
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
        print("✅ Weekly summary endpoint returned successfully")
        
        # Verify the structure of the response
        period = weekly_response.get("period")
        conversations = weekly_response.get("conversations")
        agents_created = weekly_response.get("agents_created")
        documents_created = weekly_response.get("documents_created")
        most_active_day = weekly_response.get("most_active_day")
        daily_breakdown = weekly_response.get("daily_breakdown", {})
        
        # Check period
        if period == "Last 7 days":
            print("✅ Period is correctly set to 'Last 7 days'")
        else:
            print(f"❌ Period should be 'Last 7 days', found '{period}'")
        
        # Check counts
        if isinstance(conversations, int) and isinstance(agents_created, int) and isinstance(documents_created, int):
            print("✅ Count fields have correct types")
        else:
            print("❌ Count fields have incorrect types")
        
        # Check most active day
        days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "No activity"]
        if most_active_day in days_of_week:
            print(f"✅ Most active day is valid: {most_active_day}")
        else:
            print(f"❌ Most active day is invalid: {most_active_day}")
        
        # Check daily breakdown
        if isinstance(daily_breakdown, dict) and len(daily_breakdown) <= 7:
            print(f"✅ Daily breakdown contains {len(daily_breakdown)} days")
            
            # Check if all days of the week are present
            for day in days_of_week[:7]:  # Exclude "No activity"
                if day in daily_breakdown:
                    if isinstance(daily_breakdown[day], int):
                        print(f"✅ {day} has a valid count: {daily_breakdown[day]}")
                    else:
                        print(f"❌ {day} has an invalid count type: {type(daily_breakdown[day])}")
        else:
            print(f"❌ Daily breakdown should be a dictionary with up to 7 days, found {len(daily_breakdown)} entries")
    else:
        print("❌ Weekly summary endpoint failed")
    
    # Test 3: Test authentication requirements
    print("\nTest 3: Testing authentication requirements")
    
    # Test comprehensive endpoint without auth
    no_auth_comprehensive_test, _ = run_test(
        "Comprehensive Analytics Without Authentication",
        "/analytics/comprehensive",
        method="GET",
        auth=False,
        expected_status=403
    )
    
    if no_auth_comprehensive_test:
        print("✅ Comprehensive analytics endpoint correctly requires authentication (403 Forbidden)")
    else:
        print("❌ Comprehensive analytics endpoint does not properly enforce authentication")
    
    # Test weekly summary endpoint without auth
    no_auth_weekly_test, _ = run_test(
        "Weekly Summary Without Authentication",
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
    
    # Check if all critical tests passed
    comprehensive_works = comprehensive_test
    weekly_works = weekly_test
    auth_works = no_auth_comprehensive_test and no_auth_weekly_test
    
    if comprehensive_works and weekly_works and auth_works:
        print("✅ Analytics endpoints are working correctly!")
        print("✅ Comprehensive analytics endpoint returns proper data structure")
        print("✅ Weekly summary endpoint returns proper data structure")
        print("✅ Authentication is properly enforced")
        return True, "Analytics endpoints are working correctly"
    else:
        issues = []
        if not comprehensive_works:
            issues.append("Comprehensive analytics endpoint is not functioning properly")
        if not weekly_works:
            issues.append("Weekly summary endpoint is not functioning properly")
        if not auth_works:
            issues.append("Authentication is not properly enforced for analytics endpoints")
        
        print("❌ Analytics endpoints have issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

if __name__ == "__main__":
    # Test login first to get auth token
    test_login()
    
    # Test the analytics endpoints
    analytics_success, analytics_message = test_analytics_endpoints()
    
    # Print summary
    print_summary()