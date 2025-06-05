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
    
    # 7. Generate a few conversations for summary material
    print("\nGenerating conversations for summary material...")
    for i in range(3):
        conv_gen, conv_data = run_test(
            f"Generate Conversation {i+1}",
            "/conversation/generate",
            method="POST",
            expected_keys=["messages", "round_number", "time_period"]
        )
        
        # Verify conversation has messages from all agents
        if conv_gen and len(conv_data.get("messages", [])) != 3:
            print(f"Expected messages from 3 agents, but got {len(conv_data.get('messages', []))}")
        
        # Add a small delay between conversation generations
        time.sleep(1)
    
    # 8. Test setting a custom scenario (Feature 1)
    custom_scenario = "A mysterious signal has been detected. The team must investigate."
    set_scenario, scenario_data = run_test(
        "Set Custom Scenario",
        "/simulation/set-scenario",
        method="POST",
        data={"scenario": custom_scenario},
        expected_keys=["message", "scenario"]
    )
    
    # Verify scenario was set correctly
    if set_scenario and scenario_data.get("scenario") != custom_scenario:
        print(f"Scenario was not set correctly. Expected: {custom_scenario}, Got: {scenario_data.get('scenario')}")
        set_scenario = False
    
    # 9. Test setting an empty scenario (should fail)
    empty_scenario, _ = run_test(
        "Set Empty Scenario (Should Fail)",
        "/simulation/set-scenario",
        method="POST",
        data={"scenario": ""},
        expected_status=400
    )
    
    # 10. Check simulation state to verify scenario was updated
    sim_state_updated, state_data_updated = run_test(
        "Verify Scenario Update in Simulation State",
        "/simulation/state",
        expected_keys=["current_day", "current_time_period", "is_active", "scenario"]
    )
    
    # Verify scenario was updated in simulation state
    if sim_state_updated:
        if state_data_updated.get("scenario") != custom_scenario:
            print(f"Scenario not updated in simulation state. Expected: {custom_scenario}, Got: {state_data_updated.get('scenario')}")
            sim_state_updated = False
    
    # 11. Generate weekly summary (Feature 2)
    summary_gen, summary_data = run_test(
        "Generate Weekly Summary",
        "/simulation/generate-summary",
        method="POST",
        expected_keys=["summary", "day", "conversations_count"]
    )
    
    # Verify summary was generated with meaningful content
    if summary_gen:
        if len(summary_data.get("summary", "")) < 50:
            print(f"Summary seems too short to be meaningful: {summary_data.get('summary')}")
            summary_gen = False
        else:
            print("Verified summary contains meaningful content")
            # Check for structured sections in the summary
            summary_text = summary_data.get("summary", "")
            if "KEY EVENTS & DISCOVERIES" not in summary_text or "RELATIONSHIP DEVELOPMENTS" not in summary_text:
                print("Summary doesn't contain expected structured sections")
                summary_gen = False
            else:
                print("Verified summary contains structured sections")
    
    # 12. Get all summaries (Feature 2)
    summaries, summaries_data = run_test(
        "Get All Summaries",
        "/summaries",
        expected_keys=[]  # We don't know the exact keys but expect a list
    )
    
    # Verify at least one summary exists
    if summaries:
        if not isinstance(summaries_data, list) or len(summaries_data) < 1:
            print(f"Expected at least one summary, but got: {summaries_data}")
            summaries = False
        else:
            print(f"Found {len(summaries_data)} summaries")
            # Check if the summary has the expected fields
            if "summary" not in summaries_data[0] or "day_generated" not in summaries_data[0]:
                print(f"Summary is missing expected fields: {summaries_data[0]}")
                summaries = False
            else:
                print("Verified summaries contain required fields")
    
    # 13. Test enabling auto mode (Feature 3)
    auto_mode_data = {
        "auto_conversations": True,
        "auto_time": True,
        "conversation_interval": 10,
        "time_interval": 30
    }
    auto_mode, auto_mode_response = run_test(
        "Enable Auto Mode",
        "/simulation/toggle-auto-mode",
        method="POST",
        data=auto_mode_data,
        expected_keys=["message", "auto_conversations", "auto_time", "conversation_interval", "time_interval"]
    )
    
    # Verify auto mode settings were applied
    if auto_mode:
        for key, value in auto_mode_data.items():
            if auto_mode_response.get(key) != value:
                print(f"Auto mode setting {key} was not set correctly. Expected: {value}, Got: {auto_mode_response.get(key)}")
                auto_mode = False
                break
        if auto_mode:
            print("Verified all auto mode settings were applied correctly")
    
    # 14. Test disabling auto mode (Feature 3)
    disable_auto_data = {
        "auto_conversations": False,
        "auto_time": False
    }
    disable_auto, disable_auto_response = run_test(
        "Disable Auto Mode",
        "/simulation/toggle-auto-mode",
        method="POST",
        data=disable_auto_data,
        expected_keys=["message", "auto_conversations", "auto_time"]
    )
    
    # Verify auto mode was disabled
    if disable_auto:
        if disable_auto_response.get("auto_conversations") != False or disable_auto_response.get("auto_time") != False:
            print(f"Auto mode was not disabled correctly")
            disable_auto = False
        else:
            print("Verified auto mode was disabled correctly")
    
    # 15. Check simulation state to verify auto mode settings
    sim_state_auto, state_data_auto = run_test(
        "Verify Auto Mode Settings in Simulation State",
        "/simulation/state",
        expected_keys=["current_day", "current_time_period", "is_active", "auto_conversations", "auto_time"]
    )
    
    # Verify auto mode settings in simulation state
    if sim_state_auto:
        if state_data_auto.get("auto_conversations") != False or state_data_auto.get("auto_time") != False:
            print(f"Auto mode settings not correctly reflected in simulation state")
            sim_state_auto = False
        else:
            print("Verified auto mode settings are correctly reflected in simulation state")
    
    # 16. Check API usage to verify tracking with summary generation (Feature 4)
    api_usage, usage_data = run_test(
        "Check API Usage After Summary Generation",
        "/api-usage",
        expected_keys=["date", "requests_used", "max_requests", "remaining"]
    )
    
    # Verify API usage is being tracked
    if api_usage:
        if usage_data.get("requests_used", 0) < 1:
            print("Expected API usage to be at least 1 after generating summary")
            api_usage = False
        else:
            print(f"Verified API usage is being tracked: {usage_data.get('requests_used')} requests used")
    
    # 17. Advance time period
    next_period, period_data = run_test(
        "Advance Time Period",
        "/simulation/next-period",
        method="POST",
        expected_keys=["message", "new_period"]
    )
    
    # Verify time period advanced
    if next_period:
        if state_data_auto.get("current_time_period") == period_data.get("new_period"):
            print(f"Time period did not advance, still at {period_data.get('new_period')}")
            next_period = False
        else:
            print(f"Verified time period advanced to {period_data.get('new_period')}")
    
    # 18. Check simulation state again to verify time period changed
    sim_state_final, state_data_final = run_test(
        "Verify Time Period Advanced",
        "/simulation/state",
        expected_keys=["current_day", "current_time_period", "is_active"]
    )
    
    # Verify time period changed
    if sim_state_final:
        if state_data_auto.get("current_time_period") == state_data_final.get("current_time_period"):
            print(f"Time period did not change in simulation state")
            sim_state_final = False
        else:
            print(f"Verified time period successfully advanced from {state_data_auto.get('current_time_period')} to {state_data_final.get('current_time_period')}")
    
    # Print summary of all tests
    print_summary()

if __name__ == "__main__":
    main()
