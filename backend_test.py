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
    """Run all API tests in sequence"""
    print("Starting API tests...")
    
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
    
    # 2. Test getting archetypes
    archetypes_test, archetypes_data = run_test(
        "Get Agent Archetypes",
        "/archetypes",
        expected_keys=["scientist", "artist", "leader", "skeptic", 
                      "optimist", "introvert", "adventurer", "mediator"]
    )
    
    # 3. Initialize research station
    init_station, init_data = run_test(
        "Initialize Research Station",
        "/simulation/init-research-station",
        method="POST",
        expected_keys=["message", "agents"]
    )
    
    # 4. Get all agents
    agents_test, agents_data = run_test(
        "Get All Agents",
        "/agents",
    )
    
    # Verify we have 3 agents
    if agents_test:
        if len(agents_data) != 3:
            print(f"Expected 3 agents, but got {len(agents_data)}")
            agents_test = False
        else:
            print("Verified 3 agents were created")
    
    # 5. Start simulation
    sim_start, _ = run_test(
        "Start Simulation",
        "/simulation/start",
        method="POST",
        expected_keys=["message", "state"]
    )
    
    # 6. Get simulation state
    sim_state, state_data = run_test(
        "Get Simulation State",
        "/simulation/state",
        expected_keys=["current_day", "current_time_period", "is_active"]
    )
    
    # Verify simulation is active
    if sim_state and not state_data.get("is_active", False):
        print("Simulation state shows inactive, but should be active")
        sim_state = False
    
    # 7. Generate conversation
    conv_gen, conv_data = run_test(
        "Generate Conversation",
        "/conversation/generate",
        method="POST",
        expected_keys=["messages", "round_number", "time_period"]
    )
    
    # Verify conversation has messages from all agents
    if conv_gen and len(conv_data.get("messages", [])) != 3:
        print(f"Expected messages from 3 agents, but got {len(conv_data.get('messages', []))}")
    
    # 8. Get conversation history
    conv_history, history_data = run_test(
        "Get Conversation History",
        "/conversations"
    )
    
    # Verify we have at least one conversation
    if conv_history and len(history_data) < 1:
        print("Expected at least one conversation in history")
        conv_history = False
    
    # 9. Check API usage
    api_usage, usage_data = run_test(
        "Check API Usage",
        "/api-usage",
        expected_keys=["date", "requests_used", "max_requests", "remaining"]
    )
    
    # Verify API usage is being tracked
    if api_usage:
        if usage_data.get("requests_used", 0) < 1:
            print("Expected API usage to be at least 1 after generating conversation")
    
    # 10. Generate another conversation to test multiple rounds
    print("\nGenerating second conversation round...")
    conv_gen2, conv_data2 = run_test(
        "Generate Second Conversation",
        "/conversation/generate",
        method="POST",
        expected_keys=["messages", "round_number", "time_period"]
    )
    
    # Verify round number increased
    if conv_gen2 and conv_data2.get("round_number") <= conv_data.get("round_number", 0):
        print(f"Expected round number to increase, but got {conv_data2.get('round_number')}")
    
    # 11. Advance time period
    next_period, period_data = run_test(
        "Advance Time Period",
        "/simulation/next-period",
        method="POST",
        expected_keys=["message", "new_period"]
    )
    
    # Verify time period advanced
    if next_period:
        if state_data.get("current_time_period") == period_data.get("new_period"):
            print(f"Time period did not advance, still at {period_data.get('new_period')}")
            next_period = False
    
    # 12. Check simulation state again to verify time period changed
    sim_state2, state_data2 = run_test(
        "Verify Time Period Advanced",
        "/simulation/state",
        expected_keys=["current_day", "current_time_period", "is_active"]
    )
    
    # Verify time period changed
    if sim_state2:
        if state_data.get("current_time_period") == state_data2.get("current_time_period"):
            print(f"Time period did not change in simulation state")
            sim_state2 = False
        else:
            print(f"Time period successfully advanced from {state_data.get('current_time_period')} to {state_data2.get('current_time_period')}")
    
    # Print summary of all tests
    print_summary()

if __name__ == "__main__":
    main()
