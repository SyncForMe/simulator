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
    
    # 2. Test API usage tracking
    api_usage, api_usage_data = run_test(
        "API Usage Tracking",
        "/api-usage",
        expected_keys=["date", "requests_used", "max_requests", "remaining"]
    )
    
    if api_usage:
        print(f"API Usage: {api_usage_data.get('requests_used')}/{api_usage_data.get('max_requests')} requests used")
        print(f"API Status: {'Available' if api_usage_data.get('api_available') else 'Unavailable'}")
    
    # 3. Test the complete flow of starting a new simulation
    print("\n" + "="*80)
    print("TESTING COMPLETE SIMULATION STARTUP FLOW")
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
        "scenario": "Testing the AI agent simulation with a custom scenario"
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
    else:
        print(f"Successfully set scenario: {scenario_result.get('scenario')}")
    
    # 3.4 Toggle auto mode (should enable automation)
    auto_mode_data = {
        "auto_conversations": True,
        "auto_time": True,
        "conversation_interval": 15,
        "time_interval": 45
    }
    toggle_auto, auto_result = run_test(
        "Toggle Auto Mode",
        "/simulation/toggle-auto-mode",
        method="POST",
        data=auto_mode_data,
        expected_keys=["message", "auto_conversations", "auto_time", "conversation_interval", "time_interval"]
    )
    
    if not toggle_auto:
        print("Failed to toggle auto mode. Continuing with manual mode.")
    else:
        print("Successfully enabled auto mode with the following settings:")
        print(f"  - Auto Conversations: {auto_result.get('auto_conversations')}")
        print(f"  - Auto Time: {auto_result.get('auto_time')}")
        print(f"  - Conversation Interval: {auto_result.get('conversation_interval')} seconds")
        print(f"  - Time Interval: {auto_result.get('time_interval')} seconds")
    
    # 3.5 Get simulation state (should show the updated state with automation enabled)
    sim_state, state_data = run_test(
        "Get Simulation State",
        "/simulation/state",
        expected_keys=["current_day", "current_time_period", "is_active"]
    )
    
    if sim_state:
        print("Current simulation state:")
        print(f"  - Day: {state_data.get('current_day')}")
        print(f"  - Time Period: {state_data.get('current_time_period')}")
        print(f"  - Active: {state_data.get('is_active')}")
        print(f"  - Scenario: {state_data.get('scenario')}")
        
        # Verify auto mode settings were saved
        auto_conversations = state_data.get('auto_conversations')
        auto_time = state_data.get('auto_time')
        conversation_interval = state_data.get('conversation_interval')
        time_interval = state_data.get('time_interval')
        
        if auto_conversations is None or auto_time is None:
            print("❌ Auto mode settings not found in simulation state")
            sim_state = False
        else:
            print("Auto mode settings in simulation state:")
            print(f"  - Auto Conversations: {auto_conversations}")
            print(f"  - Auto Time: {auto_time}")
            print(f"  - Conversation Interval: {conversation_interval}")
            print(f"  - Time Interval: {time_interval}")
            
            # Verify settings match what we sent
            settings_match = (
                auto_conversations == auto_mode_data["auto_conversations"] and
                auto_time == auto_mode_data["auto_time"] and
                conversation_interval == auto_mode_data["conversation_interval"] and
                time_interval == auto_mode_data["time_interval"]
            )
            
            if settings_match:
                print("✅ Auto mode settings correctly saved in simulation state")
            else:
                print("❌ Auto mode settings in simulation state don't match requested values")
                sim_state = False
    
    # 4. Generate conversation and verify actual dialogue
    print("\nTesting conversation generation after enabling auto mode...")
    conv_gen, conv_data = run_test(
        "Generate Conversation",
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
            
            # Check for generic fallback patterns
            generic_patterns = [
                "is analyzing",
                "is questioning",
                "is taking a moment",
                "is carefully considering",
                "nods thoughtfully"
            ]
            
            all_valid = True
            for i, msg in enumerate(messages):
                agent_name = msg.get("agent_name", "Unknown")
                message_text = msg.get("message", "")
                
                # Check if message is a generic fallback
                is_generic = False
                for pattern in generic_patterns:
                    if pattern in message_text:
                        is_generic = True
                        break
                
                # Check if message is too short
                is_too_short = len(message_text) < 10
                
                if is_generic or is_too_short:
                    print(f"  ❌ {agent_name}: '{message_text}' (Generic fallback or too short)")
                    all_valid = False
                else:
                    print(f"  ✅ {agent_name}: '{message_text}'")
            
            if all_valid:
                print("\nSuccess: All agent responses are actual dialogue, not generic fallbacks")
            else:
                print("\nFailed: Some agent responses are still generic fallbacks")
                conv_gen = False
    
    # 5. Get all conversations
    conversations, conversations_data = run_test(
        "Get All Conversations",
        "/conversations",
        expected_keys=[]  # We expect a list
    )
    
    # Verify conversations are returned
    if conversations:
        if not isinstance(conversations_data, list) or len(conversations_data) < 1:
            print(f"Expected at least one conversation, but got: {conversations_data}")
            conversations = False
        else:
            print(f"Found {len(conversations_data)} conversations")
            
            # Check the most recent conversation for actual dialogue
            latest_conv = conversations_data[-1]
            messages = latest_conv.get("messages", [])
            
            if len(messages) != 3:
                print(f"Expected 3 messages in the latest conversation, but got {len(messages)}")
            else:
                print("\nVerifying latest conversation has actual dialogue:")
                for msg in messages:
                    agent_name = msg.get("agent_name", "Unknown")
                    message_text = msg.get("message", "")
                    print(f"  - {agent_name}: '{message_text}'")
    
    # 6. Test relationships endpoint
    relationships, relationships_data = run_test(
        "Get Relationships",
        "/relationships",
        expected_keys=[]  # We expect a list
    )
    
    # Verify relationships are returned
    if relationships:
        if not isinstance(relationships_data, list):
            print(f"Expected a list of relationships, but got: {type(relationships_data)}")
            relationships = False
        elif len(relationships_data) < 6:  # 3 agents should have 6 relationships (3 choose 2 * 2 directions)
            print(f"Expected at least 6 relationships for 3 agents, but got {len(relationships_data)}")
            relationships = False
        else:
            print(f"Found {len(relationships_data)} relationships")
            
            # Check relationship structure
            required_fields = ["agent1_id", "agent2_id", "score", "status"]
            all_fields_present = True
            
            for rel in relationships_data[:2]:  # Check first two relationships
                for field in required_fields:
                    if field not in rel:
                        print(f"Relationship missing required field: {field}")
                        all_fields_present = False
            
            if all_fields_present:
                print("Verified relationships have all required fields")
                
                # Print some relationship details
                print("\nSample relationships:")
                for i, rel in enumerate(relationships_data[:4]):
                    print(f"  {i+1}. Agent {rel.get('agent1_id')} → Agent {rel.get('agent2_id')}: Score {rel.get('score')}, Status: {rel.get('status')}")
            else:
                relationships = False
    
    # 7. Test toggling auto mode off
    auto_mode_off_data = {
        "auto_conversations": False,
        "auto_time": False,
        "conversation_interval": 10,
        "time_interval": 30
    }
    toggle_auto_off, auto_off_result = run_test(
        "Toggle Auto Mode Off",
        "/simulation/toggle-auto-mode",
        method="POST",
        data=auto_mode_off_data,
        expected_keys=["message", "auto_conversations", "auto_time"]
    )
    
    if toggle_auto_off:
        print("Successfully disabled auto mode")
        
        # Verify auto mode is off in the simulation state
        sim_state_after, state_after_data = run_test(
            "Get Simulation State After Disabling Auto Mode",
            "/simulation/state",
            expected_keys=["current_day", "current_time_period", "is_active"]
        )
        
        if sim_state_after:
            auto_conversations_after = state_after_data.get('auto_conversations')
            auto_time_after = state_after_data.get('auto_time')
            
            if auto_conversations_after or auto_time_after:
                print("❌ Auto mode not properly disabled in simulation state")
                toggle_auto_off = False
            else:
                print("✅ Auto mode successfully disabled in simulation state")
    
    # 8. Check API usage again to verify it's being tracked
    api_usage_after, api_usage_after_data = run_test(
        "API Usage Tracking After Tests",
        "/api-usage",
        expected_keys=["date", "requests_used", "max_requests", "remaining"]
    )
    
    if api_usage and api_usage_after:
        requests_before = api_usage_data.get('requests_used', 0)
        requests_after = api_usage_after_data.get('requests_used', 0)
        
        if requests_after > requests_before:
            print(f"✅ API usage increased from {requests_before} to {requests_after} requests")
        else:
            print(f"Note: API usage didn't increase ({requests_before} → {requests_after})")
    
    # Print summary of all tests
    print_summary()

if __name__ == "__main__":
    main()
