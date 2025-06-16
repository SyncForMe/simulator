#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import base64
import re
import uuid
import jwt
from datetime import datetime, timedelta
import statistics

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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None, params=None, measure_time=False):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth and "Authorization" not in headers:
        print("Warning: Auth flag is set but no Authorization header provided")
    
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
        if isinstance(expected_status, list):
            status_ok = response.status_code in expected_status
        else:
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

def test_user_data_isolation():
    """Test user data isolation between different users"""
    print("\n" + "="*80)
    print("TESTING USER DATA ISOLATION")
    print("="*80)
    
    # Create two test users
    user1_email = f"user1.{uuid.uuid4()}@example.com"
    user1_password = "securePassword123"
    user1_name = "Test User 1"
    
    user2_email = f"user2.{uuid.uuid4()}@example.com"
    user2_password = "securePassword123"
    user2_name = "Test User 2"
    
    # Register first user
    print("\nTest 1: Register first test user")
    user1_register_data = {
        "email": user1_email,
        "password": user1_password,
        "name": user1_name
    }
    
    user1_register_test, user1_register_response = run_test(
        "Register User 1",
        "/auth/register",
        method="POST",
        data=user1_register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if not user1_register_test or not user1_register_response:
        print("❌ Failed to register first test user")
        return False, "Failed to register first test user"
    
    user1_token = user1_register_response.get("access_token")
    user1_id = user1_register_response.get("user", {}).get("id")
    print(f"✅ Registered User 1 with ID: {user1_id}")
    
    # Register second user
    print("\nTest 2: Register second test user")
    user2_register_data = {
        "email": user2_email,
        "password": user2_password,
        "name": user2_name
    }
    
    user2_register_test, user2_register_response = run_test(
        "Register User 2",
        "/auth/register",
        method="POST",
        data=user2_register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if not user2_register_test or not user2_register_response:
        print("❌ Failed to register second test user")
        return False, "Failed to register second test user"
    
    user2_token = user2_register_response.get("access_token")
    user2_id = user2_register_response.get("user", {}).get("id")
    print(f"✅ Registered User 2 with ID: {user2_id}")
    
    # Test 3: Verify new users start with empty data
    print("\nTest 3: Verify new users start with empty data")
    
    # Check User 1's documents
    user1_docs_test, user1_docs_response = run_test(
        "Get User 1 Documents",
        "/documents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    user1_initial_doc_count = 0
    if user1_docs_test and user1_docs_response:
        user1_initial_doc_count = len(user1_docs_response)
        print(f"User 1 document count: {user1_initial_doc_count}")
        if user1_initial_doc_count == 0:
            print("✅ User 1 starts with no documents")
        else:
            print(f"❌ User 1 has {user1_initial_doc_count} documents after registration")
    else:
        print("❌ Failed to get User 1's documents")
    
    # Check User 2's documents
    user2_docs_test, user2_docs_response = run_test(
        "Get User 2 Documents",
        "/documents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    
    user2_initial_doc_count = 0
    if user2_docs_test and user2_docs_response:
        user2_initial_doc_count = len(user2_docs_response)
        print(f"User 2 document count: {user2_initial_doc_count}")
        if user2_initial_doc_count == 0:
            print("✅ User 2 starts with no documents")
        else:
            print(f"❌ User 2 has {user2_initial_doc_count} documents after registration")
    else:
        print("❌ Failed to get User 2's documents")
    
    # Check User 1's saved agents
    user1_agents_test, user1_agents_response = run_test(
        "Get User 1 Saved Agents",
        "/agents/saved",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {user1_token}"},
        expected_status=[200, 404, 405]  # Allow 404/405 if endpoint not implemented
    )
    
    if user1_agents_test and user1_agents_response:
        user1_agent_count = len(user1_agents_response) if isinstance(user1_agents_response, list) else 0
        print(f"User 1 saved agent count: {user1_agent_count}")
        if user1_agent_count == 0:
            print("✅ User 1 starts with no saved agents")
        else:
            print(f"❌ User 1 has {user1_agent_count} saved agents after registration")
    else:
        print("⚠️ Could not verify User 1's saved agents - endpoint may not be implemented")
    
    # Check User 1's conversation history
    user1_convs_test, user1_convs_response = run_test(
        "Get User 1 Conversation History",
        "/conversations",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {user1_token}"},
        expected_status=[200, 404, 405]  # Allow 404/405 if endpoint not implemented
    )
    
    if user1_convs_test and user1_convs_response:
        user1_conv_count = len(user1_convs_response) if isinstance(user1_convs_response, list) else 0
        print(f"User 1 conversation count: {user1_conv_count}")
        if user1_conv_count == 0:
            print("✅ User 1 starts with no conversation history")
        else:
            print(f"❌ User 1 has {user1_conv_count} conversations after registration")
    else:
        print("⚠️ Could not verify User 1's conversation history - endpoint may not be implemented")
    
    # Test 4: Create documents for User 1
    print("\nTest 4: Create documents for User 1")
    
    user1_doc_ids = []
    for i in range(3):
        doc_data = {
            "title": f"User 1 Test Document {i+1}",
            "category": "Protocol",
            "description": f"This is test document {i+1} for User 1",
            "content": f"# User 1 Test Document {i+1}\n\nThis is test document {i+1} created by User 1.",
            "keywords": ["test", "user1"],
            "authors": ["User 1"]
        }
        
        create_doc_test, create_doc_response = run_test(
            f"Create Document {i+1} for User 1",
            "/documents/create",
            method="POST",
            data=doc_data,
            auth=True,
            headers={"Authorization": f"Bearer {user1_token}"},
            expected_keys=["success", "document_id"]
        )
        
        if create_doc_test and create_doc_response:
            doc_id = create_doc_response.get("document_id")
            if doc_id:
                print(f"✅ Created document {i+1} for User 1 with ID: {doc_id}")
                user1_doc_ids.append(doc_id)
            else:
                print(f"❌ Failed to get document ID for User 1 document {i+1}")
        else:
            print(f"❌ Failed to create document {i+1} for User 1")
    
    # Test 5: Verify User 1 can see their documents
    print("\nTest 5: Verify User 1 can see their documents")
    
    user1_docs_test, user1_docs_response = run_test(
        "Get User 1 Documents After Creation",
        "/documents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    if user1_docs_test and user1_docs_response:
        user1_doc_count = len(user1_docs_response)
        print(f"User 1 document count after creation: {user1_doc_count}")
        if user1_doc_count == len(user1_doc_ids) + user1_initial_doc_count:
            print(f"✅ User 1 can see all {len(user1_doc_ids)} of their documents")
        else:
            print(f"❌ User 1 sees {user1_doc_count} documents but created {len(user1_doc_ids)}")
    else:
        print("❌ Failed to get User 1's documents after creation")
    
    # Test 6: Verify User 2 cannot see User 1's documents
    print("\nTest 6: Verify User 2 cannot see User 1's documents")
    
    user2_docs_test, user2_docs_response = run_test(
        "Get User 2 Documents",
        "/documents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    
    if user2_docs_test and user2_docs_response:
        user2_doc_count = len(user2_docs_response)
        print(f"User 2 document count: {user2_doc_count}")
        if user2_doc_count == user2_initial_doc_count:
            print("✅ User 2 cannot see User 1's documents")
        else:
            print(f"❌ User 2 can see {user2_doc_count - user2_initial_doc_count} documents that should be isolated to User 1")
    else:
        print("❌ Failed to get User 2's documents")
    
    # Test 7: Verify User 2 cannot access User 1's document directly
    print("\nTest 7: Verify User 2 cannot access User 1's document directly")
    
    if user1_doc_ids:
        user1_doc_id = user1_doc_ids[0]
        
        user2_access_test, user2_access_response = run_test(
            "User 2 Accessing User 1's Document",
            f"/documents/{user1_doc_id}",
            method="GET",
            auth=True,
            headers={"Authorization": f"Bearer {user2_token}"},
            expected_status=404  # Should return 404 Not Found
        )
        
        if user2_access_test:
            print("✅ User 2 cannot access User 1's document directly")
        else:
            print("❌ User 2 can access User 1's document directly")
    else:
        print("⚠️ Skipping direct document access test - no documents created for User 1")
    
    # Test 8: Create documents for User 2
    print("\nTest 8: Create documents for User 2")
    
    user2_doc_ids = []
    for i in range(2):
        doc_data = {
            "title": f"User 2 Test Document {i+1}",
            "category": "Research",
            "description": f"This is test document {i+1} for User 2",
            "content": f"# User 2 Test Document {i+1}\n\nThis is test document {i+1} created by User 2.",
            "keywords": ["test", "user2"],
            "authors": ["User 2"]
        }
        
        create_doc_test, create_doc_response = run_test(
            f"Create Document {i+1} for User 2",
            "/documents/create",
            method="POST",
            data=doc_data,
            auth=True,
            headers={"Authorization": f"Bearer {user2_token}"},
            expected_keys=["success", "document_id"]
        )
        
        if create_doc_test and create_doc_response:
            doc_id = create_doc_response.get("document_id")
            if doc_id:
                print(f"✅ Created document {i+1} for User 2 with ID: {doc_id}")
                user2_doc_ids.append(doc_id)
            else:
                print(f"❌ Failed to get document ID for User 2 document {i+1}")
        else:
            print(f"❌ Failed to create document {i+1} for User 2")
    
    # Test 9: Verify User 1 cannot see User 2's documents
    print("\nTest 9: Verify User 1 cannot see User 2's documents")
    
    user1_docs_test, user1_docs_response = run_test(
        "Get User 1 Documents After User 2 Creation",
        "/documents",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    
    if user1_docs_test and user1_docs_response:
        user1_doc_count = len(user1_docs_response)
        print(f"User 1 document count: {user1_doc_count}")
        if user1_doc_count == len(user1_doc_ids) + user1_initial_doc_count:
            print("✅ User 1 can only see their own documents")
        else:
            print(f"❌ User 1 sees {user1_doc_count} documents but should only see {len(user1_doc_ids) + user1_initial_doc_count}")
    else:
        print("❌ Failed to get User 1's documents")
    
    # Test 10: Verify User 1 cannot access User 2's document directly
    print("\nTest 10: Verify User 1 cannot access User 2's document directly")
    
    if user2_doc_ids:
        user2_doc_id = user2_doc_ids[0]
        
        user1_access_test, user1_access_response = run_test(
            "User 1 Accessing User 2's Document",
            f"/documents/{user2_doc_id}",
            method="GET",
            auth=True,
            headers={"Authorization": f"Bearer {user1_token}"},
            expected_status=404  # Should return 404 Not Found
        )
        
        if user1_access_test:
            print("✅ User 1 cannot access User 2's document directly")
        else:
            print("❌ User 1 can access User 2's document directly")
    else:
        print("⚠️ Skipping direct document access test - no documents created for User 2")
    
    # Print summary
    print("\nUSER DATA ISOLATION SUMMARY:")
    
    # Check if all tests passed
    new_user_empty_data = (
        (user1_docs_test and user1_initial_doc_count == 0) and
        (user2_docs_test and user2_initial_doc_count == 0)
    )
    
    cross_user_isolation = (
        (user2_docs_test and len(user2_docs_response) == user2_initial_doc_count + len(user2_doc_ids)) and
        (user1_docs_test and len(user1_docs_response) == user1_initial_doc_count + len(user1_doc_ids))
    )
    
    if new_user_empty_data:
        print("✅ New users start with empty data")
    else:
        print("❌ New users do not start with empty data")
    
    if cross_user_isolation:
        print("✅ User data is properly isolated between users")
    else:
        print("❌ User data is not properly isolated between users")
    
    return new_user_empty_data and cross_user_isolation, {
        "new_user_empty_data": new_user_empty_data,
        "cross_user_isolation": cross_user_isolation
    }

def test_admin_functionality():
    """Test admin functionality with the dino@cytonic.com account"""
    print("\n" + "="*80)
    print("TESTING ADMIN FUNCTIONALITY")
    print("="*80)
    
    # Create a regular test user for comparison
    regular_user_email = f"regular.user.{uuid.uuid4()}@example.com"
    regular_user_password = "securePassword123"
    regular_user_name = "Regular User"
    
    # Register regular user
    print("\nTest 1: Register regular test user")
    regular_user_register_data = {
        "email": regular_user_email,
        "password": regular_user_password,
        "name": regular_user_name
    }
    
    regular_user_register_test, regular_user_register_response = run_test(
        "Register Regular User",
        "/auth/register",
        method="POST",
        data=regular_user_register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if not regular_user_register_test or not regular_user_register_response:
        print("❌ Failed to register regular test user")
        return False, "Failed to register regular test user"
    
    regular_user_token = regular_user_register_response.get("access_token")
    regular_user_id = regular_user_register_response.get("user", {}).get("id")
    print(f"✅ Registered Regular User with ID: {regular_user_id}")
    
    # Register admin user (dino@cytonic.com)
    print("\nTest 2: Register/login admin user (dino@cytonic.com)")
    admin_user_email = "dino@cytonic.com"
    admin_user_password = "adminPassword123"
    admin_user_name = "Admin User"
    
    admin_user_register_data = {
        "email": admin_user_email,
        "password": admin_user_password,
        "name": admin_user_name
    }
    
    # Try to register the admin user (may fail if already exists)
    admin_register_test, admin_register_response = run_test(
        "Register Admin User",
        "/auth/register",
        method="POST",
        data=admin_user_register_data,
        expected_status=[200, 400]  # Allow both success and "user already exists"
    )
    
    # If registration failed (user exists), try logging in
    if not admin_register_test or not admin_register_response or (isinstance(admin_register_response, dict) and admin_register_response.get("detail", "").startswith("User with email")):
        print("Admin user registration failed or user already exists, trying login...")
        admin_login_data = {
            "email": admin_user_email,
            "password": admin_user_password
        }
        
        admin_login_test, admin_login_response = run_test(
            "Login Admin User",
            "/auth/login",
            method="POST",
            data=admin_login_data,
            expected_keys=["access_token", "token_type", "user"]
        )
        
        if not admin_login_test or not admin_login_response:
            print("❌ Failed to login as admin user")
            print("⚠️ Creating a new admin user with the correct email...")
            
            # Try with a different password
            admin_user_register_data["password"] = "adminSecurePassword456"
            admin_register_test, admin_register_response = run_test(
                "Register Admin User (Second Attempt)",
                "/auth/register",
                method="POST",
                data=admin_user_register_data,
                expected_keys=["access_token", "token_type", "user"]
            )
            
            if not admin_register_test or not admin_register_response:
                print("❌ Failed to register admin user")
                return False, "Failed to register/login admin user"
            
            admin_user_token = admin_register_response.get("access_token")
            admin_user_id = admin_register_response.get("user", {}).get("id")
        else:
            admin_user_token = admin_login_response.get("access_token")
            admin_user_id = admin_login_response.get("user", {}).get("id")
    else:
        admin_user_token = admin_register_response.get("access_token")
        admin_user_id = admin_register_response.get("user", {}).get("id")
    
    print(f"✅ Admin user authenticated with ID: {admin_user_id}")
    
    # Test 3: Test admin dashboard stats endpoint with admin user
    print("\nTest 3: Test admin dashboard stats endpoint with admin user")
    
    admin_stats_test, admin_stats_response = run_test(
        "Admin Dashboard Stats",
        "/admin/dashboard/stats",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {admin_user_token}"},
        expected_keys=["overview"]
    )
    
    if admin_stats_test and admin_stats_response:
        print("✅ Admin user can access dashboard stats")
        overview = admin_stats_response.get("overview", {})
        print("Dashboard Stats Overview:")
        for key, value in overview.items():
            print(f"  - {key}: {value}")
    else:
        print("❌ Admin user cannot access dashboard stats")
    
    # Test 4: Test admin users endpoint with admin user
    print("\nTest 4: Test admin users endpoint with admin user")
    
    admin_users_test, admin_users_response = run_test(
        "Admin Users List",
        "/admin/users",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {admin_user_token}"},
        expected_keys=["users", "pagination"]
    )
    
    if admin_users_test and admin_users_response:
        print("✅ Admin user can access users list")
        users = admin_users_response.get("users", [])
        print(f"Total users: {len(users)}")
        if users:
            print("Sample user data:")
            for key, value in users[0].items():
                if key != "stats":
                    print(f"  - {key}: {value}")
                else:
                    print(f"  - {key}:")
                    for stat_key, stat_value in value.items():
                        print(f"    - {stat_key}: {stat_value}")
    else:
        print("❌ Admin user cannot access users list")
    
    # Test 5: Test admin recent activity endpoint with admin user
    print("\nTest 5: Test admin recent activity endpoint with admin user")
    
    admin_activity_test, admin_activity_response = run_test(
        "Admin Recent Activity",
        "/admin/activity/recent",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {admin_user_token}"},
        expected_keys=["recent_users", "recent_documents", "recent_agents"]
    )
    
    if admin_activity_test and admin_activity_response:
        print("✅ Admin user can access recent activity")
        recent_users = admin_activity_response.get("recent_users", [])
        recent_documents = admin_activity_response.get("recent_documents", [])
        recent_agents = admin_activity_response.get("recent_agents", [])
        
        print(f"Recent users: {len(recent_users)}")
        print(f"Recent documents: {len(recent_documents)}")
        print(f"Recent agents: {len(recent_agents)}")
    else:
        print("❌ Admin user cannot access recent activity")
    
    # Test 6: Test admin endpoints with regular user (should be forbidden)
    print("\nTest 6: Test admin endpoints with regular user (should be forbidden)")
    
    # Test dashboard stats with regular user
    regular_stats_test, regular_stats_response = run_test(
        "Regular User Accessing Dashboard Stats",
        "/admin/dashboard/stats",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {regular_user_token}"},
        expected_status=403  # Should be forbidden
    )
    
    if regular_stats_test:
        print("✅ Regular user correctly denied access to dashboard stats")
    else:
        print("❌ Regular user not properly restricted from dashboard stats")
    
    # Test users list with regular user
    regular_users_test, regular_users_response = run_test(
        "Regular User Accessing Users List",
        "/admin/users",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {regular_user_token}"},
        expected_status=403  # Should be forbidden
    )
    
    if regular_users_test:
        print("✅ Regular user correctly denied access to users list")
    else:
        print("❌ Regular user not properly restricted from users list")
    
    # Test recent activity with regular user
    regular_activity_test, regular_activity_response = run_test(
        "Regular User Accessing Recent Activity",
        "/admin/activity/recent",
        method="GET",
        auth=True,
        headers={"Authorization": f"Bearer {regular_user_token}"},
        expected_status=403  # Should be forbidden
    )
    
    if regular_activity_test:
        print("✅ Regular user correctly denied access to recent activity")
    else:
        print("❌ Regular user not properly restricted from recent activity")
    
    # Print summary
    print("\nADMIN FUNCTIONALITY SUMMARY:")
    
    # Check if all tests passed
    admin_access_works = admin_stats_test and admin_users_test and admin_activity_test
    regular_user_restricted = regular_stats_test and regular_users_test and regular_activity_test
    
    if admin_access_works:
        print("✅ Admin user (dino@cytonic.com) can access all admin endpoints")
    else:
        print("❌ Admin user cannot access all admin endpoints")
    
    if regular_user_restricted:
        print("✅ Regular users are properly restricted from admin endpoints")
    else:
        print("❌ Regular users are not properly restricted from admin endpoints")
    
    return admin_access_works and regular_user_restricted, {
        "admin_access_works": admin_access_works,
        "regular_user_restricted": regular_user_restricted
    }

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING USER ISOLATION TESTS")
    print("="*80)
    
    # Test user data isolation
    user_isolation_success, user_isolation_results = test_user_data_isolation()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("USER ISOLATION ASSESSMENT")
    print("="*80)
    
    if user_isolation_success:
        print("✅ User data isolation is working correctly")
        print("✅ New users start with empty data")
        print("✅ Users cannot access each other's data")
    else:
        print("❌ User data isolation has issues")
        if isinstance(user_isolation_results, dict):
            if not user_isolation_results.get("new_user_empty_data"):
                print("  - New users do not start with empty data")
            if not user_isolation_results.get("cross_user_isolation"):
                print("  - Users can access each other's data")
    
    print("="*80)
    
    return user_isolation_success

if __name__ == "__main__":
    main()