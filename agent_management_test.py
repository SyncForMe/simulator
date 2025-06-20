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
created_agent_id = None
saved_agent_id = None

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

def test_register_user():
    """Register a new test user"""
    global auth_token, test_user_id
    
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
    
    if register_test and register_response:
        print("✅ Registration successful")
        auth_token = register_response.get("access_token")
        user_data = register_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"User registered with ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        return True
    else:
        print("❌ Registration failed")
        return False

def test_login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    # Try using the email/password login first
    login_data = {
        "email": test_user_email,
        "password": test_user_password
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

def test_create_agent():
    """Create a test agent"""
    global created_agent_id
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot create test agent without authentication")
            return False
    
    # Create a test agent
    agent_data = {
        "name": f"Test Agent {uuid.uuid4().hex[:8]}",
        "archetype": "scientist",
        "personality": {
            "extroversion": 7,
            "optimism": 8,
            "curiosity": 9,
            "cooperativeness": 6,
            "energy": 7
        },
        "goal": "To test the agent management functionality",
        "expertise": "Software Testing",
        "background": "Experienced in testing APIs and backend systems",
        "memory_summary": "Created for testing agent update functionality",
        "avatar_prompt": "A professional software tester with glasses"
    }
    
    create_agent_test, create_agent_response = run_test(
        "Create Test Agent",
        "/agents",
        method="POST",
        data=agent_data,
        auth=True,
        expected_keys=["id", "name", "archetype"]
    )
    
    if create_agent_test and create_agent_response:
        created_agent_id = create_agent_response.get("id")
        print(f"✅ Created test agent with ID: {created_agent_id}")
        return True
    else:
        print("❌ Failed to create test agent")
        return False

def test_update_agent():
    """Test updating an agent's details"""
    global created_agent_id
    
    # Create an agent first if needed
    if not created_agent_id:
        if not test_create_agent():
            print("❌ Cannot test agent update without a test agent")
            return False
    
    # Update the agent's details
    update_data = {
        "name": f"Updated Agent {uuid.uuid4().hex[:8]}",
        "archetype": "leader",
        "personality": {
            "extroversion": 9,
            "optimism": 9,
            "curiosity": 7,
            "cooperativeness": 8,
            "energy": 9
        },
        "goal": "To verify the agent update functionality works correctly",
        "expertise": "API Testing and Verification",
        "background": "Updated background information for testing",
        "memory_summary": "Memory updated during testing"
    }
    
    update_agent_test, update_agent_response = run_test(
        "Update Agent",
        f"/agents/{created_agent_id}",
        method="PUT",
        data=update_data,
        auth=True,
        expected_keys=["id", "name", "archetype"]
    )
    
    if update_agent_test and update_agent_response:
        # Verify the update was successful
        if update_agent_response.get("name") == update_data["name"] and \
           update_agent_response.get("archetype") == update_data["archetype"] and \
           update_agent_response.get("goal") == update_data["goal"]:
            print("✅ Agent update was successful")
            return True
        else:
            print("❌ Agent update was not applied correctly")
            return False
    else:
        print("❌ Failed to update agent")
        return False

def test_save_agent_to_library():
    """Test saving an agent to the user's library"""
    global created_agent_id, saved_agent_id
    
    # Create an agent first if needed
    if not created_agent_id:
        if not test_create_agent():
            print("❌ Cannot test saving agent without a test agent")
            return False
    
    # Since there's no GET endpoint for individual agents, we'll create a new agent data
    # directly for saving to the library
    save_data = {
        "name": f"Saved Agent {uuid.uuid4().hex[:8]}",
        "archetype": "scientist",
        "personality": {
            "extroversion": 7,
            "optimism": 8,
            "curiosity": 9,
            "cooperativeness": 6,
            "energy": 7
        },
        "goal": "To test the saved agent functionality",
        "expertise": "Software Testing",
        "background": "Experienced in testing APIs and backend systems",
        "avatar_url": "",
        "avatar_prompt": "A professional software tester with glasses",
        "is_template": False
    }
    
    save_agent_test, save_agent_response = run_test(
        "Save Agent to Library",
        "/saved-agents",
        method="POST",
        data=save_data,
        auth=True,
        expected_keys=["id", "name", "user_id"]
    )
    
    if save_agent_test and save_agent_response:
        saved_agent_id = save_agent_response.get("id")
        print(f"✅ Saved agent to library with ID: {saved_agent_id}")
        
        # Verify the saved agent belongs to the current user
        if save_agent_response.get("user_id") == test_user_id:
            print("✅ Saved agent is correctly associated with the current user")
            return True
        else:
            print("❌ Saved agent is not correctly associated with the current user")
            return False
    else:
        print("❌ Failed to save agent to library")
        return False

def test_get_saved_agents():
    """Test retrieving the user's saved agents"""
    global saved_agent_id
    
    # Save an agent first if needed
    if not saved_agent_id:
        if not test_save_agent_to_library():
            print("❌ Cannot test getting saved agents without a saved agent")
            return False
    
    # Get the user's saved agents
    get_saved_agents_test, get_saved_agents_response = run_test(
        "Get Saved Agents",
        "/saved-agents",
        method="GET",
        auth=True
    )
    
    if get_saved_agents_test and get_saved_agents_response:
        # Verify the saved agent is in the list
        saved_agent_found = False
        for agent in get_saved_agents_response:
            if agent.get("id") == saved_agent_id:
                saved_agent_found = True
                break
        
        if saved_agent_found:
            print("✅ Saved agent found in the user's library")
            return True
        else:
            print("❌ Saved agent not found in the user's library")
            return False
    else:
        print("❌ Failed to get saved agents")
        return False

def test_update_saved_agent():
    """Test updating a saved agent's details"""
    global saved_agent_id
    
    # Save an agent first if needed
    if not saved_agent_id:
        if not test_save_agent_to_library():
            print("❌ Cannot test updating saved agent without a saved agent")
            return False
    
    # Update the saved agent's details
    update_data = {
        "name": f"Updated Saved Agent {uuid.uuid4().hex[:8]}",
        "archetype": "optimist",
        "personality": {
            "extroversion": 8,
            "optimism": 10,
            "curiosity": 7,
            "cooperativeness": 9,
            "energy": 8
        },
        "goal": "To verify the saved agent update functionality works correctly",
        "expertise": "Updated expertise for testing",
        "background": "Updated background for saved agent testing",
        "avatar_url": "",
        "avatar_prompt": "A cheerful optimist with a bright smile"
    }
    
    update_saved_agent_test, update_saved_agent_response = run_test(
        "Update Saved Agent",
        f"/saved-agents/{saved_agent_id}",
        method="PUT",
        data=update_data,
        auth=True,
        expected_keys=["id", "name", "user_id"]
    )
    
    if update_saved_agent_test and update_saved_agent_response:
        # Verify the update was successful
        if update_saved_agent_response.get("name") == update_data["name"] and \
           update_saved_agent_response.get("archetype") == update_data["archetype"] and \
           update_saved_agent_response.get("goal") == update_data["goal"]:
            print("✅ Saved agent update was successful")
            return True
        else:
            print("❌ Saved agent update was not applied correctly")
            return False
    else:
        print("❌ Failed to update saved agent")
        return False

def test_delete_saved_agent():
    """Test deleting a saved agent"""
    global saved_agent_id
    
    # Save an agent first if needed
    if not saved_agent_id:
        if not test_save_agent_to_library():
            print("❌ Cannot test deleting saved agent without a saved agent")
            return False
    
    # Delete the saved agent
    delete_saved_agent_test, delete_saved_agent_response = run_test(
        "Delete Saved Agent",
        f"/saved-agents/{saved_agent_id}",
        method="DELETE",
        auth=True,
        expected_keys=["message"]
    )
    
    if delete_saved_agent_test and delete_saved_agent_response:
        print("✅ Saved agent deleted successfully")
        
        # Verify the agent is actually deleted
        get_saved_agents_test, get_saved_agents_response = run_test(
            "Verify Saved Agent Deletion",
            "/saved-agents",
            method="GET",
            auth=True
        )
        
        if get_saved_agents_test and get_saved_agents_response is not None:
            # Check if the deleted agent is still in the list
            agent_found = False
            for agent in get_saved_agents_response:
                if agent.get("id") == saved_agent_id:
                    agent_found = True
                    break
            
            if not agent_found:
                print("✅ Saved agent confirmed deleted")
                return True
            else:
                print("❌ Saved agent still exists after deletion")
                return False
        else:
            print("❌ Failed to verify saved agent deletion")
            return False
    else:
        print("❌ Failed to delete saved agent")
        return False

def test_authentication_flow():
    """Test the authentication flow for agent management endpoints"""
    
    # Create a test agent without authentication
    agent_data = {
        "name": f"Unauthorized Agent {uuid.uuid4().hex[:8]}",
        "archetype": "scientist",
        "personality": {
            "extroversion": 5,
            "optimism": 5,
            "curiosity": 5,
            "cooperativeness": 5,
            "energy": 5
        },
        "goal": "To test authentication",
        "expertise": "Authentication Testing",
        "background": "Testing authentication flow"
    }
    
    # Test creating agent without auth
    no_auth_create_test, _ = run_test(
        "Create Agent Without Auth",
        "/agents",
        method="POST",
        data=agent_data,
        expected_status=403  # Should fail with 403 Forbidden
    )
    
    if no_auth_create_test:
        print("✅ Creating agent without authentication correctly fails")
    else:
        print("❌ Creating agent without authentication does not fail as expected")
    
    # Test getting saved agents without auth
    no_auth_get_test, _ = run_test(
        "Get Saved Agents Without Auth",
        "/saved-agents",
        method="GET",
        expected_status=403  # Should fail with 403 Forbidden
    )
    
    if no_auth_get_test:
        print("✅ Getting saved agents without authentication correctly fails")
    else:
        print("❌ Getting saved agents without authentication does not fail as expected")
    
    # Test with invalid token
    invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpbnZhbGlkQGV4YW1wbGUuY29tIiwidXNlcl9pZCI6ImludmFsaWQtdXNlci1pZCIsImV4cCI6MTcxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    invalid_token_test, _ = run_test(
        "Get Saved Agents With Invalid Token",
        "/saved-agents",
        method="GET",
        headers={"Authorization": f"Bearer {invalid_token}"},
        expected_status=401  # Should fail with 401 Unauthorized
    )
    
    if invalid_token_test:
        print("✅ Using invalid token correctly fails")
    else:
        print("❌ Using invalid token does not fail as expected")
    
    return no_auth_create_test and no_auth_get_test and invalid_token_test

def test_agent_management_workflow():
    """Test the complete agent management workflow"""
    
    # Step 1: Register a new user
    print("\n" + "="*80)
    print("STEP 1: Register a new user")
    print("="*80)
    register_success = test_register_user()
    
    if not register_success:
        print("❌ Failed to register user, cannot continue workflow test")
        return False
    
    # Step 2: Create an agent
    print("\n" + "="*80)
    print("STEP 2: Create an agent")
    print("="*80)
    create_success = test_create_agent()
    
    if not create_success:
        print("❌ Failed to create agent, cannot continue workflow test")
        return False
    
    # Step 3: Update the agent's details
    print("\n" + "="*80)
    print("STEP 3: Update the agent's details")
    print("="*80)
    update_success = test_update_agent()
    
    if not update_success:
        print("❌ Failed to update agent, continuing workflow test")
    
    # Step 4: Save the agent to library
    print("\n" + "="*80)
    print("STEP 4: Save the agent to library")
    print("="*80)
    save_success = test_save_agent_to_library()
    
    if not save_success:
        print("❌ Failed to save agent to library, cannot continue workflow test")
        return False
    
    # Step 5: Retrieve saved agents
    print("\n" + "="*80)
    print("STEP 5: Retrieve saved agents")
    print("="*80)
    get_success = test_get_saved_agents()
    
    if not get_success:
        print("❌ Failed to retrieve saved agents, continuing workflow test")
    
    # Step 6: Update saved agent details
    print("\n" + "="*80)
    print("STEP 6: Update saved agent details")
    print("="*80)
    update_saved_success = test_update_saved_agent()
    
    if not update_saved_success:
        print("❌ Failed to update saved agent, continuing workflow test")
    
    # Step 7: Delete saved agent
    print("\n" + "="*80)
    print("STEP 7: Delete saved agent")
    print("="*80)
    delete_success = test_delete_saved_agent()
    
    if not delete_success:
        print("❌ Failed to delete saved agent")
    
    # Print workflow summary
    print("\n" + "="*80)
    print("AGENT MANAGEMENT WORKFLOW SUMMARY")
    print("="*80)
    
    workflow_steps = [
        ("Register User", register_success),
        ("Create Agent", create_success),
        ("Update Agent", update_success),
        ("Save Agent to Library", save_success),
        ("Retrieve Saved Agents", get_success),
        ("Update Saved Agent", update_saved_success),
        ("Delete Saved Agent", delete_success)
    ]
    
    for step, success in workflow_steps:
        result = "✅ PASSED" if success else "❌ FAILED"
        print(f"{step}: {result}")
    
    overall_success = all([
        register_success,
        create_success,
        save_success
    ])
    
    print("\nOverall Workflow: " + ("✅ PASSED" if overall_success else "❌ FAILED"))
    return overall_success

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TESTING AGENT MANAGEMENT FUNCTIONALITY")
    print("="*80)
    
    # Test authentication flow
    print("\n" + "="*80)
    print("TESTING AUTHENTICATION FLOW")
    print("="*80)
    auth_flow_success = test_authentication_flow()
    
    # Test complete workflow
    print("\n" + "="*80)
    print("TESTING COMPLETE AGENT MANAGEMENT WORKFLOW")
    print("="*80)
    workflow_success = test_agent_management_workflow()
    
    # Print overall summary
    print_summary()
    
    return auth_flow_success and workflow_success

if __name__ == "__main__":
    main()