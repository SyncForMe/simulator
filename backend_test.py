#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv

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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        else:
            print(f"Unsupported method: {method}")
            return False
        
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
        
        test_results["tests"].append({
            "name": test_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "result": result
        })
        
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

def main():
    """Run API tests focused on API usage limits and conversation generation"""
    print("Starting API tests for API usage limits and conversation generation...")
    
    # 1. Test basic health check
    health_check, _ = run_test(
        "Basic API Health Check", 
        "/", 
        expected_keys=["message"]
    )
    
    if not health_check:
        print("Health check failed. Aborting remaining tests.")
        print_summary()
        return
    
    # 2. Test API usage tracking - check current usage and verify new max limit (50000)
    api_usage, api_usage_data = run_test(
        "API Usage Tracking",
        "/api-usage",
        expected_keys=["date", "requests_used", "max_requests", "remaining"]
    )
    
    if api_usage:
        print(f"API Usage: {api_usage_data.get('requests_used')}/{api_usage_data.get('max_requests')} requests used")
        print(f"API Status: {'Available' if api_usage_data.get('api_available') else 'Unavailable'}")
        
        # Verify the max_requests is now 50000 (updated from 1400)
        max_requests = api_usage_data.get('max_requests', 0)
        if max_requests == 50000:
            print("✅ Max daily requests correctly set to 50000")
        else:
            print(f"❌ Max daily requests is {max_requests}, expected 50000")
            api_usage = False
    
    # 3. Test the simulation setup flow to prepare for conversation generation tests
    print("\n" + "="*80)
    print("SETTING UP SIMULATION FOR CONVERSATION GENERATION TESTS")
    print("="*80)
    
    # 3.1 Start simulation (should clear everything and reset state)
    sim_start, sim_start_data = run_test(
        "Start New Simulation",
        "/simulation/start",
        method="POST",
        expected_keys=["message", "state"]
    )
    
    if not sim_start:
        print("Failed to start simulation. Aborting remaining tests.")
        print_summary()
        return
    
    # 3.2 Initialize research station (should create default agents)
    init_station, init_data = run_test(
        "Initialize Research Station",
        "/simulation/init-research-station",
        method="POST",
        expected_keys=["message", "agents"]
    )
    
    if not init_station:
        print("Failed to initialize research station. Aborting remaining tests.")
        print_summary()
        return
    
    # Verify we have 3 agents with correct names
    agents = init_data.get("agents", [])
    if len(agents) != 3:
        print(f"Expected 3 agents, but got {len(agents)}")
        init_station = False
    else:
        print("Verified 3 agents were created:")
        for agent in agents:
            print(f"  - {agent.get('name')} ({agent.get('archetype')})")
    
    # 3.3 Set scenario
    scenario_data = {
        "scenario": "Testing the AI agent simulation with increased API limits"
    }
    set_scenario, scenario_result = run_test(
        "Set Custom Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=scenario_data,
        expected_keys=["message", "scenario"]
    )
    
    if not set_scenario:
        print("Failed to set scenario. Continuing with default scenario.")
    
    # 4. Generate multiple conversations to test the new API limits
    print("\n" + "="*80)
    print("TESTING CONVERSATION GENERATION WITH NEW API LIMITS")
    print("="*80)
    
    # Track if any conversation generation fails due to API limits
    any_limit_reached = False
    
    # Generate 5 conversations in sequence
    for i in range(5):
        print(f"\nGenerating conversation {i+1}/5...")
        conv_gen, conv_data = run_test(
            f"Generate Conversation {i+1}",
            "/conversation/generate",
            method="POST",
            expected_keys=["messages", "round_number", "time_period"]
        )
        
        # Verify conversation has messages from all agents
        if conv_gen:
            messages = conv_data.get("messages", [])
            if len(messages) != 3:
                print(f"Expected messages from 3 agents, but got {len(messages)}")
                conv_gen = False
            else:
                print("\nVerifying agent responses are actual dialogue (not generic fallbacks):")
                
                # Check for generic fallback patterns and API limit messages
                generic_patterns = [
                    "is analyzing",
                    "is questioning",
                    "is taking a moment",
                    "is carefully considering",
                    "nods thoughtfully",
                    "daily API limit reached"
                ]
                
                all_valid = True
                for i, msg in enumerate(messages):
                    agent_name = msg.get("agent_name", "Unknown")
                    message_text = msg.get("message", "")
                    
                    # Check if message is a generic fallback or mentions API limits
                    is_generic = False
                    is_limit_message = False
                    for pattern in generic_patterns:
                        if pattern in message_text:
                            is_generic = True
                            if "daily API limit reached" in message_text:
                                is_limit_message = True
                                any_limit_reached = True
                            break
                    
                    # Check if message is too short
                    is_too_short = len(message_text) < 10
                    
                    if is_limit_message:
                        print(f"  ❌ {agent_name}: '{message_text}' (API LIMIT REACHED MESSAGE DETECTED)")
                        all_valid = False
                    elif is_generic or is_too_short:
                        print(f"  ❌ {agent_name}: '{message_text}' (Generic fallback or too short)")
                        all_valid = False
                    else:
                        print(f"  ✅ {agent_name}: '{message_text}'")
                
                if all_valid:
                    print("\nSuccess: All agent responses are actual dialogue, not generic fallbacks")
                else:
                    print("\nFailed: Some agent responses are still generic fallbacks or API limit messages")
                    conv_gen = False
        
        # Add a short delay between conversation generations
        time.sleep(2)
    
    # 5. Check API usage after generating conversations
    api_usage_after, api_usage_after_data = run_test(
        "API Usage After Generating Conversations",
        "/api-usage",
        expected_keys=["date", "requests_used", "max_requests", "remaining"]
    )
    
    if api_usage and api_usage_after:
        requests_before = api_usage_data.get('requests_used', 0)
        requests_after = api_usage_after_data.get('requests_used', 0)
        max_requests = api_usage_after_data.get('max_requests', 0)
        remaining = api_usage_after_data.get('remaining', 0)
        
        print("\n" + "="*80)
        print("API USAGE ANALYSIS")
        print("="*80)
        print(f"Initial API usage: {requests_before} requests")
        print(f"Current API usage: {requests_after} requests")
        print(f"Requests used during test: {requests_after - requests_before} requests")
        print(f"Max daily requests: {max_requests} requests")
        print(f"Remaining requests: {remaining} requests")
        print(f"API available: {api_usage_after_data.get('api_available')}")
        
        if requests_after > requests_before:
            print(f"✅ API usage increased from {requests_before} to {requests_after} requests")
            
            # Check if we're approaching the limit
            usage_percentage = (requests_after / max_requests) * 100
            print(f"Current usage: {usage_percentage:.2f}% of daily limit")
            
            if usage_percentage > 90:
                print("⚠️ Warning: API usage is above 90% of daily limit")
            elif usage_percentage > 75:
                print("⚠️ Warning: API usage is above 75% of daily limit")
        else:
            print(f"Note: API usage didn't increase ({requests_before} → {requests_after})")
    
    # 6. Final verification of API limit messages
    if any_limit_reached:
        print("\n❌ Some conversations still showed 'daily API limit reached' messages")
        print("This suggests the API limit issue is not fully resolved")
    else:
        print("\n✅ No 'daily API limit reached' messages detected in any conversations")
        print("The increased API limit (50000) appears to be working correctly")
    
    # 7. Get all conversations to verify they were stored correctly
    conversations, conversations_data = run_test(
        "Get All Conversations",
        "/conversations",
        expected_keys=[]  # We expect a list
    )
    
    # Verify conversations are returned
    if conversations:
        if not isinstance(conversations_data, list):
            print(f"Expected a list of conversations, but got: {type(conversations_data)}")
            conversations = False
        else:
            print(f"Found {len(conversations_data)} conversations in the database")
    
    # Print summary of all tests
    print_summary()

if __name__ == "__main__":
    main()
