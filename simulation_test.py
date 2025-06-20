#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid

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
    
    # Try using the email/password login first with admin credentials
    login_data = {
        "email": "dino@cytonic.com",
        "password": "Observerinho8"
    }
    
    login_test, login_response = run_test(
        "Login with admin credentials",
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

def test_simulation_workflow():
    """Test the complete simulation workflow"""
    print("\n" + "="*80)
    print("TESTING SIMULATION WORKFLOW")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test simulation workflow without authentication")
            return False, "Authentication failed"
    
    # Test 1: Start New Simulation
    print("\nTest 1: Starting a new simulation")
    
    simulation_start_test, simulation_start_response = run_test(
        "Start Simulation",
        "/simulation/start",
        method="POST",
        auth=True,
        expected_keys=["message", "state"]
    )
    
    if not simulation_start_test:
        print("❌ Failed to start simulation")
        return False, "Failed to start simulation"
    
    print("✅ Successfully started simulation")
    
    # Test 2: Get Simulation State
    print("\nTest 2: Getting simulation state")
    
    state_test, state_response = run_test(
        "Get Simulation State",
        "/simulation/state",
        method="GET",
        auth=True
    )
    
    if not state_test:
        print("❌ Failed to get simulation state")
        return False, "Failed to get simulation state"
    
    print("✅ Successfully retrieved simulation state")
    
    # Test 3: Create agents
    print("\nTest 3: Creating agents")
    
    # Create a test agent
    agent_data = {
        "name": "Test Agent",
        "archetype": "scientist",
        "personality": {
            "extroversion": 5,
            "optimism": 7,
            "curiosity": 9,
            "cooperativeness": 6,
            "energy": 8
        },
        "goal": "Test the simulation workflow",
        "expertise": "Testing and Quality Assurance",
        "background": "Experienced in testing complex systems",
        "memory_summary": "Focused on ensuring all systems work correctly",
        "avatar_prompt": "Professional QA engineer with glasses"
    }
    
    create_agent_test, create_agent_response = run_test(
        "Create Agent",
        "/agents",
        method="POST",
        data=agent_data,
        auth=True,
        expected_keys=["id", "name"]
    )
    
    if not create_agent_test:
        print("❌ Failed to create agent")
        return False, "Failed to create agent"
    
    agent_id = create_agent_response.get("id")
    print(f"✅ Successfully created agent with ID: {agent_id}")
    
    # Create a second agent for conversation generation
    agent2_data = {
        "name": "Second Test Agent",
        "archetype": "leader",
        "personality": {
            "extroversion": 8,
            "optimism": 8,
            "curiosity": 6,
            "cooperativeness": 7,
            "energy": 9
        },
        "goal": "Lead the simulation testing",
        "expertise": "Project Management",
        "background": "Experienced in leading complex projects",
        "memory_summary": "Focused on coordinating testing efforts",
        "avatar_prompt": "Confident project manager in business attire"
    }
    
    create_agent2_test, create_agent2_response = run_test(
        "Create Second Agent",
        "/agents",
        method="POST",
        data=agent2_data,
        auth=True,
        expected_keys=["id", "name"]
    )
    
    if not create_agent2_test:
        print("❌ Failed to create second agent")
        return False, "Failed to create second agent"
    
    agent2_id = create_agent2_response.get("id")
    print(f"✅ Successfully created second agent with ID: {agent2_id}")
    
    # Test 4: Set Random Scenario
    print("\nTest 4: Setting a random scenario")
    
    # Get a random scenario first
    random_scenario_test, random_scenario_response = run_test(
        "Get Random Scenario",
        "/simulation/random-scenario",
        method="GET",
        auth=True,
        expected_keys=["scenario", "scenario_name"]
    )
    
    if not random_scenario_test:
        print("❌ Failed to get random scenario")
        return False, "Failed to get random scenario"
    
    scenario = random_scenario_response.get("scenario")
    scenario_name = random_scenario_response.get("scenario_name")
    print(f"✅ Successfully retrieved random scenario: {scenario_name}")
    
    # Set the scenario
    set_scenario_data = {
        "scenario": scenario,
        "scenario_name": scenario_name
    }
    
    set_scenario_test, set_scenario_response = run_test(
        "Set Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=set_scenario_data,
        auth=True,
        expected_keys=["message", "scenario", "scenario_name"]
    )
    
    if not set_scenario_test:
        print("❌ Failed to set scenario")
        return False, "Failed to set scenario"
    
    print(f"✅ Successfully set scenario: {scenario_name}")
    
    # Test 5: Generate Conversation
    print("\nTest 5: Generating a conversation")
    
    generate_conversation_test, generate_conversation_response = run_test(
        "Generate Conversation",
        "/conversation/generate",
        method="POST",
        auth=True,
        expected_keys=["messages", "round_number", "scenario"],
        measure_time=True
    )
    
    if not generate_conversation_test:
        print("❌ Failed to generate conversation")
        return False, "Failed to generate conversation"
    
    conversation_round = generate_conversation_response.get("round_number")
    messages = generate_conversation_response.get("messages", [])
    print(f"✅ Successfully generated conversation round {conversation_round} with {len(messages)} messages")
    
    # Test 6: Pause Simulation
    print("\nTest 6: Pausing the simulation")
    
    pause_test, pause_response = run_test(
        "Pause Simulation",
        "/simulation/pause",
        method="POST",
        auth=True,
        expected_keys=["message", "is_active"]
    )
    
    if not pause_test:
        print("❌ Failed to pause simulation")
        return False, "Failed to pause simulation"
    
    is_active = pause_response.get("is_active")
    if is_active:
        print("❌ Simulation is still active after pause")
    else:
        print("✅ Successfully paused simulation")
    
    # Test 7: Resume Simulation
    print("\nTest 7: Resuming the simulation")
    
    resume_test, resume_response = run_test(
        "Resume Simulation",
        "/simulation/resume",
        method="POST",
        auth=True,
        expected_keys=["message", "is_active"]
    )
    
    if not resume_test:
        print("❌ Failed to resume simulation")
        return False, "Failed to resume simulation"
    
    is_active = resume_response.get("is_active")
    if not is_active:
        print("❌ Simulation is still paused after resume")
    else:
        print("✅ Successfully resumed simulation")
    
    # Print summary
    print("\nSIMULATION WORKFLOW SUMMARY:")
    
    # Check if all tests passed
    all_passed = (
        simulation_start_test and
        state_test and
        create_agent_test and
        create_agent2_test and
        random_scenario_test and
        set_scenario_test and
        generate_conversation_test and
        pause_test and
        resume_test
    )
    
    if all_passed:
        print("✅ Complete simulation workflow is working correctly!")
        print("✅ Successfully started simulation")
        print("✅ Successfully retrieved simulation state")
        print("✅ Successfully created agents")
        print("✅ Successfully set random scenario")
        print("✅ Successfully generated conversation")
        print("✅ Successfully paused and resumed simulation")
        return True, "Complete simulation workflow is working correctly"
    else:
        issues = []
        if not simulation_start_test:
            issues.append("Failed to start simulation")
        if not state_test:
            issues.append("Failed to get simulation state")
        if not create_agent_test or not create_agent2_test:
            issues.append("Failed to create agents")
        if not random_scenario_test:
            issues.append("Failed to get random scenario")
        if not set_scenario_test:
            issues.append("Failed to set scenario")
        if not generate_conversation_test:
            issues.append("Failed to generate conversation")
        if not pause_test or not resume_test:
            issues.append("Failed to pause or resume simulation")
        
        print("❌ Simulation workflow has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

if __name__ == "__main__":
    # Run the tests
    test_login()
    test_simulation_workflow()
    print_summary()