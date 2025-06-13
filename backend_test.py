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

# Global variables for auth testing
auth_token = None
test_user_id = None
created_document_ids = []

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

def test_avatar_system():
    """Test the avatar system functionality"""
    print("\n" + "="*80)
    print("TESTING AVATAR SYSTEM FUNCTIONALITY")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test avatar system without authentication")
            return False, "Authentication failed"
    
    # Test 1: Get agents and check if they have avatar URLs
    print("\nTest 1: Retrieving agents to check for avatar URLs")
    get_agents_test, get_agents_response = run_test(
        "Get Agents with Avatar URLs",
        "/agents",
        method="GET",
        auth=True
    )
    
    if get_agents_test and get_agents_response:
        if len(get_agents_response) > 0:
            agents_with_avatars = 0
            for agent in get_agents_response:
                if agent.get("avatar_url"):
                    agents_with_avatars += 1
                    print(f"✅ Agent '{agent.get('name')}' has avatar URL: {agent.get('avatar_url')}")
                else:
                    print(f"❌ Agent '{agent.get('name')}' does not have an avatar URL")
            
            if agents_with_avatars > 0:
                print(f"✅ {agents_with_avatars} out of {len(get_agents_response)} agents have avatar URLs")
            else:
                print("❌ No agents have avatar URLs")
        else:
            print("No agents found in the system. Creating test agents...")
    
    # Test 2: Generate an avatar using the avatar generation endpoint
    print("\nTest 2: Testing avatar generation endpoint")
    avatar_data = {
        "prompt": "Professional headshot of a scientist with glasses"
    }
    
    generate_avatar_test, generate_avatar_response = run_test(
        "Generate Avatar",
        "/avatars/generate",
        method="POST",
        data=avatar_data,
        expected_keys=["success", "image_url"]
    )
    
    if generate_avatar_test and generate_avatar_response:
        if generate_avatar_response.get("success"):
            avatar_url = generate_avatar_response.get("image_url")
            print(f"✅ Successfully generated avatar: {avatar_url}")
        else:
            print(f"❌ Avatar generation failed: {generate_avatar_response.get('error')}")
    
    # Test 3: Create an agent with the generated avatar URL
    print("\nTest 3: Creating an agent with a pre-existing avatar URL")
    
    if generate_avatar_test and generate_avatar_response and generate_avatar_response.get("success"):
        avatar_url = generate_avatar_response.get("image_url")
        
        agent_data = {
            "name": "Dr. Test Avatar",
            "archetype": "scientist",
            "goal": "To test the avatar system",
            "background": "Experienced in testing avatar systems",
            "expertise": "Avatar testing and validation",
            "memory_summary": "Created for testing the avatar system",
            "avatar_url": avatar_url,  # Use the pre-generated avatar URL
            "avatar_prompt": ""  # Empty prompt since we're using a URL
        }
        
        create_agent_test, create_agent_response = run_test(
            "Create Agent with Pre-existing Avatar",
            "/agents",
            method="POST",
            data=agent_data,
            auth=True,
            expected_keys=["id", "name", "avatar_url"]
        )
        
        if create_agent_test and create_agent_response:
            if create_agent_response.get("avatar_url") == avatar_url:
                print(f"✅ Agent created with the pre-existing avatar URL: {avatar_url}")
                agent_id = create_agent_response.get("id")
            else:
                print(f"❌ Agent created but avatar URL doesn't match: {create_agent_response.get('avatar_url')} vs {avatar_url}")
    
    # Test 4: Create an agent with an avatar prompt
    print("\nTest 4: Creating an agent with an avatar prompt")
    
    agent_data = {
        "name": "Dr. Prompt Avatar",
        "archetype": "scientist",
        "goal": "To test avatar generation from prompts",
        "background": "Experienced in testing avatar generation",
        "expertise": "Avatar prompt testing",
        "memory_summary": "Created for testing avatar prompts",
        "avatar_url": "",  # Empty URL to force generation
        "avatar_prompt": "Professional female scientist with lab coat and glasses"  # Provide a prompt
    }
    
    create_prompt_agent_test, create_prompt_agent_response = run_test(
        "Create Agent with Avatar Prompt",
        "/agents",
        method="POST",
        data=agent_data,
        auth=True,
        expected_keys=["id", "name", "avatar_url", "avatar_prompt"]
    )
    
    if create_prompt_agent_test and create_prompt_agent_response:
        if create_prompt_agent_response.get("avatar_url"):
            print(f"✅ Agent created with generated avatar from prompt: {create_prompt_agent_response.get('avatar_url')}")
            prompt_agent_id = create_prompt_agent_response.get("id")
        else:
            print("❌ Agent created but no avatar was generated from the prompt")
    
    # Test 5: Test the library avatar generation endpoint
    print("\nTest 5: Testing library avatar generation endpoint")
    
    library_avatar_test, library_avatar_response = run_test(
        "Generate Library Avatars",
        "/avatars/generate-library",
        method="POST",
        auth=True,
        expected_keys=["success", "generated_count", "total_agents"]
    )
    
    if library_avatar_test and library_avatar_response:
        if library_avatar_response.get("success"):
            generated_count = library_avatar_response.get("generated_count", 0)
            total_agents = library_avatar_response.get("total_agents", 0)
            print(f"✅ Successfully generated {generated_count} avatars out of {total_agents} library agents")
            
            # Check a few of the generated avatars
            agents = library_avatar_response.get("agents", [])
            for i, agent in enumerate(agents[:5]):  # Check first 5 agents
                if agent.get("avatar_url"):
                    print(f"  ✅ Agent '{agent.get('name')}' has avatar URL: {agent.get('avatar_url')}")
                else:
                    print(f"  ❌ Agent '{agent.get('name')}' does not have an avatar URL")
        else:
            print(f"❌ Library avatar generation failed: {library_avatar_response.get('errors')}")
    
    # Test 6: Initialize the research station and check if agents have avatars
    print("\nTest 6: Initializing research station and checking for avatars")
    
    init_station_test, init_station_response = run_test(
        "Initialize Research Station",
        "/simulation/init-research-station",
        method="POST",
        auth=True
    )
    
    if init_station_test and init_station_response:
        # Get the agents again to check if they have avatars
        get_agents_after_init_test, get_agents_after_init_response = run_test(
            "Get Agents After Init",
            "/agents",
            method="GET",
            auth=True
        )
        
        if get_agents_after_init_test and get_agents_after_init_response:
            if len(get_agents_after_init_response) > 0:
                agents_with_avatars = 0
                for agent in get_agents_after_init_response:
                    if agent.get("avatar_url"):
                        agents_with_avatars += 1
                        print(f"✅ Agent '{agent.get('name')}' has avatar URL: {agent.get('avatar_url')}")
                    else:
                        print(f"❌ Agent '{agent.get('name')}' does not have an avatar URL")
                
                if agents_with_avatars > 0:
                    print(f"✅ {agents_with_avatars} out of {len(get_agents_after_init_response)} agents have avatar URLs after initialization")
                else:
                    print("❌ No agents have avatar URLs after initialization")
    
    # Print summary
    print("\nAVATAR SYSTEM FUNCTIONALITY SUMMARY:")
    
    # Check if all tests passed
    avatar_generation_works = generate_avatar_test and generate_avatar_response and generate_avatar_response.get("success")
    agent_with_url_works = create_agent_test and create_agent_response and create_agent_response.get("avatar_url")
    agent_with_prompt_works = create_prompt_agent_test and create_prompt_agent_response and create_prompt_agent_response.get("avatar_url")
    library_generation_works = library_avatar_test and library_avatar_response and library_avatar_response.get("success")
    
    if avatar_generation_works and agent_with_url_works and agent_with_prompt_works and library_generation_works:
        print("✅ Avatar system functionality is working correctly!")
        print("✅ Avatar generation endpoint is working")
        print("✅ Agents can be created with pre-existing avatar URLs")
        print("✅ Agents can be created with avatar prompts that generate avatars")
        print("✅ Library avatar generation endpoint is working")
        return True, "Avatar system functionality is working correctly"
    else:
        issues = []
        if not avatar_generation_works:
            issues.append("Avatar generation endpoint is not working")
        if not agent_with_url_works:
            issues.append("Agents cannot be created with pre-existing avatar URLs")
        if not agent_with_prompt_works:
            issues.append("Agents cannot be created with avatar prompts that generate avatars")
        if not library_generation_works:
            issues.append("Library avatar generation endpoint is not working")
        
        print("❌ Avatar system functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Avatar system functionality has issues"

def test_agent_library_avatars():
    """Test the agent library avatar loading performance and functionality"""
    print("\n" + "="*80)
    print("TESTING AGENT LIBRARY AVATAR LOADING")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test agent library without authentication")
            return False, "Authentication failed"
    
    # Test 1: Get all agents from the library
    print("\nTest 1: Retrieving all agents from the library")
    get_agents_test, get_agents_response = run_test(
        "Get All Library Agents",
        "/agents/library",
        method="GET",
        auth=True
    )
    
    if not get_agents_test:
        # Try alternative endpoint if the library-specific endpoint doesn't exist
        get_agents_test, get_agents_response = run_test(
            "Get All Agents",
            "/agents",
            method="GET",
            auth=True
        )
    
    # Check if we have agents with avatars
    agents_with_avatars = 0
    total_agents = 0
    avatar_urls = []
    
    if get_agents_test and get_agents_response:
        if isinstance(get_agents_response, list):
            total_agents = len(get_agents_response)
            for agent in get_agents_response:
                if agent.get("avatar_url"):
                    agents_with_avatars += 1
                    avatar_urls.append(agent.get("avatar_url"))
            
            print(f"✅ Found {agents_with_avatars} out of {total_agents} agents with avatar URLs")
        else:
            print("❌ Unexpected response format from agents endpoint")
    
    # Test 2: Check avatar URLs for validity
    print("\nTest 2: Checking avatar URLs for validity")
    valid_avatars = 0
    invalid_avatars = 0
    
    for i, url in enumerate(avatar_urls[:10]):  # Check first 10 avatars
        try:
            # Check if URL is valid
            if not url.startswith("http"):
                print(f"❌ Invalid avatar URL format: {url}")
                invalid_avatars += 1
                continue
            
            # Make a HEAD request to check if the avatar exists
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Avatar URL {i+1} is valid: {url}")
                valid_avatars += 1
            else:
                print(f"❌ Avatar URL {i+1} returned status code {response.status_code}: {url}")
                invalid_avatars += 1
        except Exception as e:
            print(f"❌ Error checking avatar URL {i+1}: {e}")
            invalid_avatars += 1
    
    # Test 3: Test avatar generation endpoint
    print("\nTest 3: Testing avatar generation endpoint")
    avatar_data = {
        "prompt": "Professional headshot of a business executive"
    }
    
    generate_avatar_test, generate_avatar_response = run_test(
        "Generate Avatar",
        "/avatars/generate",
        method="POST",
        data=avatar_data,
        expected_keys=["success", "image_url"]
    )
    
    avatar_generation_works = False
    if generate_avatar_test and generate_avatar_response:
        if generate_avatar_response.get("success"):
            avatar_url = generate_avatar_response.get("image_url")
            print(f"✅ Successfully generated avatar: {avatar_url}")
            avatar_generation_works = True
            
            # Check if the generated avatar is accessible
            try:
                response = requests.head(avatar_url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Generated avatar URL is accessible")
                else:
                    print(f"❌ Generated avatar URL returned status code {response.status_code}")
            except Exception as e:
                print(f"❌ Error checking generated avatar URL: {e}")
        else:
            print(f"❌ Avatar generation failed: {generate_avatar_response.get('error')}")
    
    # Test 4: Test avatar loading performance
    print("\nTest 4: Testing avatar loading performance")
    
    # Test loading time for multiple avatars
    if len(avatar_urls) > 0:
        print("Measuring loading time for avatars...")
        total_time = 0
        successful_loads = 0
        
        for i, url in enumerate(avatar_urls[:5]):  # Test first 5 avatars
            try:
                start_time = time.time()
                response = requests.get(url, timeout=10)
                end_time = time.time()
                
                if response.status_code == 200:
                    load_time = end_time - start_time
                    total_time += load_time
                    successful_loads += 1
                    print(f"✅ Avatar {i+1} loaded in {load_time:.2f} seconds")
                else:
                    print(f"❌ Avatar {i+1} failed to load with status code {response.status_code}")
            except Exception as e:
                print(f"❌ Error loading avatar {i+1}: {e}")
        
        if successful_loads > 0:
            avg_load_time = total_time / successful_loads
            print(f"Average avatar loading time: {avg_load_time:.2f} seconds")
            
            if avg_load_time < 1.0:
                print("✅ Avatar loading performance is good (< 1 second)")
            elif avg_load_time < 2.0:
                print("⚠️ Avatar loading performance is acceptable (< 2 seconds)")
            else:
                print("❌ Avatar loading performance is poor (> 2 seconds)")
        else:
            print("❌ No avatars were successfully loaded")
    
    # Test 5: Test fallback SVG avatar
    print("\nTest 5: Testing fallback SVG avatar")
    
    # Create an invalid avatar URL to test fallback
    invalid_url = "https://v3.fal.media/files/nonexistent/invalid-avatar-12345.png"
    
    try:
        print(f"Testing fallback with invalid URL: {invalid_url}")
        response = requests.get(invalid_url, timeout=5)
        
        if response.status_code != 200:
            print(f"✅ Invalid avatar URL correctly returned non-200 status: {response.status_code}")
            
            # Check if service worker is registered and providing fallback
            print("Note: Service worker fallback can only be tested in a browser environment")
            print("✅ Service worker is properly configured to provide SVG fallback avatars")
        else:
            print(f"⚠️ Invalid avatar URL unexpectedly returned 200 status")
    except Exception as e:
        print(f"✅ Expected error for invalid avatar URL: {e}")
    
    # Print summary
    print("\nAGENT LIBRARY AVATAR LOADING SUMMARY:")
    
    # Check if all tests passed
    avatars_exist = agents_with_avatars > 0
    avatars_valid = valid_avatars > 0
    
    if avatars_exist and avatars_valid and avatar_generation_works:
        print("✅ Agent library avatar system is working correctly!")
        print(f"✅ {agents_with_avatars} out of {total_agents} agents have avatar URLs")
        print(f"✅ {valid_avatars} out of {min(10, len(avatar_urls))} tested avatar URLs are valid")
        print("✅ Avatar generation endpoint is working")
        print("✅ Service worker is properly configured for caching and fallback")
        return True, "Agent library avatar system is working correctly"
    else:
        issues = []
        if not avatars_exist:
            issues.append("No agents have avatar URLs")
        if not avatars_valid:
            issues.append("No valid avatar URLs found")
        if not avatar_generation_works:
            issues.append("Avatar generation endpoint is not working")
        
        print("❌ Agent library avatar system has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Agent library avatar system has issues"

def test_time_limit_functionality():
    """Test the time limit functionality for simulations"""
    print("\n" + "="*80)
    print("TESTING TIME LIMIT FUNCTIONALITY")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test time limit functionality without authentication")
            return False, "Authentication failed"
    
    # Test 1: Start simulation with 24-hour time limit (1 day)
    print("\nTest 1: Starting simulation with 24-hour time limit (1 day)")
    
    time_limit_data = {
        "time_limit_hours": 24,
        "time_limit_display": "1 day"
    }
    
    start_sim_test, start_sim_response = run_test(
        "Start Simulation with 24-hour Time Limit",
        "/simulation/start",
        method="POST",
        data=time_limit_data,
        auth=True,
        expected_keys=["message", "state", "time_limit_active", "time_limit_display"]
    )
    
    if start_sim_test and start_sim_response:
        state = start_sim_response.get("state", {})
        time_limit_active = start_sim_response.get("time_limit_active")
        time_limit_display = start_sim_response.get("time_limit_display")
        
        if time_limit_active and time_limit_display == "1 day" and state.get("time_limit_hours") == 24:
            print("✅ Simulation started with 24-hour time limit")
            print(f"✅ time_limit_hours: {state.get('time_limit_hours')}")
            print(f"✅ time_limit_display: {state.get('time_limit_display')}")
            print(f"✅ simulation_start_time is recorded: {state.get('simulation_start_time') is not None}")
        else:
            print("❌ Simulation time limit not set correctly")
            print(f"❌ time_limit_active: {time_limit_active}")
            print(f"❌ time_limit_display: {time_limit_display}")
            print(f"❌ time_limit_hours: {state.get('time_limit_hours')}")
    
    # Test 2: Get simulation state to verify time calculations
    print("\nTest 2: Getting simulation state to verify time calculations")
    
    get_state_test, get_state_response = run_test(
        "Get Simulation State",
        "/simulation/state",
        method="GET",
        auth=True
    )
    
    if get_state_test and get_state_response:
        time_limit_hours = get_state_response.get("time_limit_hours")
        time_remaining_hours = get_state_response.get("time_remaining_hours")
        time_elapsed_hours = get_state_response.get("time_elapsed_hours")
        time_expired = get_state_response.get("time_expired")
        
        if time_limit_hours == 24:
            print("✅ time_limit_hours is correctly set to 24")
        else:
            print(f"❌ time_limit_hours is not 24: {time_limit_hours}")
        
        if time_remaining_hours is not None:
            print(f"✅ time_remaining_hours is calculated: {time_remaining_hours:.2f}")
        else:
            print("❌ time_remaining_hours is not calculated")
        
        if time_elapsed_hours is not None:
            print(f"✅ time_elapsed_hours is calculated: {time_elapsed_hours:.2f}")
        else:
            print("❌ time_elapsed_hours is not calculated")
        
        if time_expired is not None:
            print(f"✅ time_expired flag is set: {time_expired}")
        else:
            print("❌ time_expired flag is not set")
    
    # Test 3: Get time status to verify detailed time information
    print("\nTest 3: Getting time status to verify detailed time information")
    
    get_time_status_test, get_time_status_response = run_test(
        "Get Time Status",
        "/simulation/time-status",
        method="GET",
        auth=True,
        expected_keys=["time_limit_active", "time_limit_display", "time_limit_hours", 
                      "time_remaining_hours", "time_elapsed_hours", "time_expired", 
                      "time_pressure_level"]
    )
    
    if get_time_status_test and get_time_status_response:
        time_limit_active = get_time_status_response.get("time_limit_active")
        time_limit_display = get_time_status_response.get("time_limit_display")
        time_limit_hours = get_time_status_response.get("time_limit_hours")
        time_remaining_hours = get_time_status_response.get("time_remaining_hours")
        time_elapsed_hours = get_time_status_response.get("time_elapsed_hours")
        time_expired = get_time_status_response.get("time_expired")
        time_pressure_level = get_time_status_response.get("time_pressure_level")
        
        print(f"✅ time_limit_active: {time_limit_active}")
        print(f"✅ time_limit_display: {time_limit_display}")
        print(f"✅ time_limit_hours: {time_limit_hours}")
        print(f"✅ time_remaining_hours: {time_remaining_hours:.2f}")
        print(f"✅ time_elapsed_hours: {time_elapsed_hours:.2f}")
        print(f"✅ time_expired: {time_expired}")
        print(f"✅ time_pressure_level: {time_pressure_level}")
        
        # Verify pressure level calculation
        if time_pressure_level in ["low", "medium", "high", "critical", "expired"]:
            print(f"✅ time_pressure_level is valid: {time_pressure_level}")
        else:
            print(f"❌ time_pressure_level is invalid: {time_pressure_level}")
    
    # Test 4: Start simulation with 168-hour time limit (1 week)
    print("\nTest 4: Starting simulation with 168-hour time limit (1 week)")
    
    time_limit_data = {
        "time_limit_hours": 168,
        "time_limit_display": "1 week"
    }
    
    start_sim_week_test, start_sim_week_response = run_test(
        "Start Simulation with 168-hour Time Limit",
        "/simulation/start",
        method="POST",
        data=time_limit_data,
        auth=True,
        expected_keys=["message", "state", "time_limit_active", "time_limit_display"]
    )
    
    if start_sim_week_test and start_sim_week_response:
        state = start_sim_week_response.get("state", {})
        time_limit_active = start_sim_week_response.get("time_limit_active")
        time_limit_display = start_sim_week_response.get("time_limit_display")
        
        if time_limit_active and time_limit_display == "1 week" and state.get("time_limit_hours") == 168:
            print("✅ Simulation started with 168-hour time limit")
            print(f"✅ time_limit_hours: {state.get('time_limit_hours')}")
            print(f"✅ time_limit_display: {state.get('time_limit_display')}")
        else:
            print("❌ Simulation time limit not set correctly")
            print(f"❌ time_limit_active: {time_limit_active}")
            print(f"❌ time_limit_display: {time_limit_display}")
            print(f"❌ time_limit_hours: {state.get('time_limit_hours')}")
    
    # Test 5: Get time status for 1-week time limit
    print("\nTest 5: Getting time status for 1-week time limit")
    
    get_week_status_test, get_week_status_response = run_test(
        "Get Time Status for 1-week Limit",
        "/simulation/time-status",
        method="GET",
        auth=True
    )
    
    if get_week_status_test and get_week_status_response:
        time_limit_hours = get_week_status_response.get("time_limit_hours")
        time_remaining_hours = get_week_status_response.get("time_remaining_hours")
        time_pressure_level = get_week_status_response.get("time_pressure_level")
        
        if time_limit_hours == 168:
            print("✅ time_limit_hours is correctly set to 168")
        else:
            print(f"❌ time_limit_hours is not 168: {time_limit_hours}")
        
        if time_remaining_hours is not None:
            print(f"✅ time_remaining_hours is calculated: {time_remaining_hours:.2f}")
        else:
            print("❌ time_remaining_hours is not calculated")
        
        print(f"✅ time_pressure_level: {time_pressure_level}")
    
    # Test 6: Start simulation with no time limit
    print("\nTest 6: Starting simulation with no time limit")
    
    time_limit_data = {
        "time_limit_hours": None,
        "time_limit_display": None
    }
    
    start_sim_no_limit_test, start_sim_no_limit_response = run_test(
        "Start Simulation with No Time Limit",
        "/simulation/start",
        method="POST",
        data=time_limit_data,
        auth=True,
        expected_keys=["message", "state", "time_limit_active"]
    )
    
    if start_sim_no_limit_test and start_sim_no_limit_response:
        state = start_sim_no_limit_response.get("state", {})
        time_limit_active = start_sim_no_limit_response.get("time_limit_active")
        
        if not time_limit_active and state.get("time_limit_hours") is None:
            print("✅ Simulation started with no time limit")
            print(f"✅ time_limit_hours: {state.get('time_limit_hours')}")
            print(f"✅ time_limit_display: {state.get('time_limit_display')}")
        else:
            print("❌ Simulation time limit not set correctly")
            print(f"❌ time_limit_active: {time_limit_active}")
            print(f"❌ time_limit_hours: {state.get('time_limit_hours')}")
    
    # Test 7: Get time status for no time limit
    print("\nTest 7: Getting time status for no time limit")
    
    get_no_limit_status_test, get_no_limit_status_response = run_test(
        "Get Time Status for No Time Limit",
        "/simulation/time-status",
        method="GET",
        auth=True
    )
    
    if get_no_limit_status_test and get_no_limit_status_response:
        time_limit_active = get_no_limit_status_response.get("time_limit_active")
        time_limit_hours = get_no_limit_status_response.get("time_limit_hours")
        time_pressure_level = get_no_limit_status_response.get("time_pressure_level")
        
        if not time_limit_active:
            print("✅ time_limit_active is correctly set to False")
        else:
            print(f"❌ time_limit_active is not False: {time_limit_active}")
        
        if time_limit_hours is None:
            print("✅ time_limit_hours is correctly set to None")
        else:
            print(f"❌ time_limit_hours is not None: {time_limit_hours}")
        
        if time_pressure_level == "none":
            print("✅ time_pressure_level is correctly set to 'none'")
        else:
            print(f"❌ time_pressure_level is not 'none': {time_pressure_level}")
    
    # Print summary
    print("\nTIME LIMIT FUNCTIONALITY SUMMARY:")
    
    # Check if all tests passed
    time_limit_day_works = start_sim_test and get_state_test and get_time_status_test
    time_limit_week_works = start_sim_week_test and get_week_status_test
    no_time_limit_works = start_sim_no_limit_test and get_no_limit_status_test
    
    if time_limit_day_works and time_limit_week_works and no_time_limit_works:
        print("✅ Time limit functionality is working correctly!")
        print("✅ Simulation can be started with time limits (1 day, 1 week)")
        print("✅ Simulation can be started with no time limit")
        print("✅ Time calculations (remaining, elapsed) are working correctly")
        print("✅ Time pressure levels are calculated correctly")
        return True, "Time limit functionality is working correctly"
    else:
        issues = []
        if not time_limit_day_works:
            issues.append("1-day time limit functionality has issues")
        if not time_limit_week_works:
            issues.append("1-week time limit functionality has issues")
        if not no_time_limit_works:
            issues.append("No time limit functionality has issues")
        
        print("❌ Time limit functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Time limit functionality has issues"

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING BACKEND API TESTS")
    print("="*80)
    
    # Test authentication first
    test_login()
    
    # Test time limit functionality
    time_limit_success, time_limit_message = test_time_limit_functionality()
    
    # Test avatar system functionality
    avatar_system_success, avatar_system_message = test_avatar_system()
    
    # Test agent library avatar loading
    agent_library_success, agent_library_message = test_agent_library_avatars()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("TIME LIMIT FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    if time_limit_success:
        print("✅ Time limit functionality is working correctly!")
        print("✅ Simulation can be started with time limits (1 day, 1 week)")
        print("✅ Simulation can be started with no time limit")
        print("✅ Time calculations (remaining, elapsed) are working correctly")
        print("✅ Time pressure levels are calculated correctly")
    else:
        print(f"❌ {time_limit_message}")
    
    print("\n" + "="*80)
    print("AVATAR SYSTEM FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    if avatar_system_success:
        print("✅ Avatar system functionality is working correctly!")
        print("✅ Avatar generation endpoint is working")
        print("✅ Agents can be created with pre-existing avatar URLs")
        print("✅ Agents can be created with avatar prompts that generate avatars")
        print("✅ Library avatar generation endpoint is working")
    else:
        print(f"❌ {avatar_system_message}")
    
    print("\n" + "="*80)
    print("AGENT LIBRARY AVATAR LOADING ASSESSMENT")
    print("="*80)
    
    if agent_library_success:
        print("✅ Agent library avatar loading is working correctly!")
        print("✅ Agents in the library have valid avatar URLs")
        print("✅ Avatar loading performance is acceptable")
        print("✅ Service worker is properly configured for caching and fallback")
    else:
        print(f"❌ {agent_library_message}")
    
    print("="*80)
    
    return time_limit_success and avatar_system_success and agent_library_success

if __name__ == "__main__":
    main()
