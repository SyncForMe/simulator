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
    
    # 2. Initialize research station (create the 3 agents)
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
    
    # 3. Start simulation
    sim_start, _ = run_test(
        "Start Simulation",
        "/simulation/start",
        method="POST",
        expected_keys=["message", "state"]
    )
    
    if not sim_start:
        print("Failed to start simulation. Aborting remaining tests.")
        print_summary()
        return
    
    # 4. Generate conversation and verify actual dialogue
    print("\nTesting conversation generation fix...")
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
    
    # 7. Generate another conversation to verify consistency
    print("\nGenerating another conversation to verify consistency...")
    conv_gen2, conv_data2 = run_test(
        "Generate Second Conversation",
        "/conversation/generate",
        method="POST",
        expected_keys=["messages", "round_number", "time_period"]
    )
    
    # Verify second conversation also has actual dialogue
    if conv_gen2:
        messages = conv_data2.get("messages", [])
        if len(messages) != 3:
            print(f"Expected messages from 3 agents, but got {len(messages)}")
            conv_gen2 = False
        else:
            print("\nVerifying second conversation responses:")
            
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
                print("\nSuccess: Second conversation also has actual dialogue")
            else:
                print("\nFailed: Second conversation has some generic fallbacks")
                conv_gen2 = False
    
    # 8. Check relationships again to verify they're being updated
    relationships2, relationships_data2 = run_test(
        "Check Relationships After Second Conversation",
        "/relationships",
        expected_keys=[]  # We expect a list
    )
    
    # Verify relationships are still valid
    if relationships2 and relationships:
        print("\nVerifying relationships are properly updated after conversations:")
        
        # Compare with previous relationships
        if len(relationships_data2) != len(relationships_data):
            print(f"Relationship count changed unexpectedly: {len(relationships_data)} → {len(relationships_data2)}")
        else:
            print(f"Relationship count remained consistent: {len(relationships_data2)}")
            
            # Check if any scores changed (they should after conversation)
            score_changes = 0
            for i, (rel1, rel2) in enumerate(zip(relationships_data, relationships_data2)):
                if rel1.get("agent1_id") == rel2.get("agent1_id") and rel1.get("agent2_id") == rel2.get("agent2_id"):
                    if rel1.get("score") != rel2.get("score"):
                        score_changes += 1
                        print(f"  - Relationship {rel1.get('agent1_id')} → {rel1.get('agent2_id')} score changed: {rel1.get('score')} → {rel2.get('score')}")
            
            if score_changes > 0:
                print(f"Success: {score_changes} relationship scores were updated after conversation")
            else:
                print("Note: No relationship scores changed after conversation (this might be expected based on compatibility)")
    
    # Print summary of all tests
    print_summary()

if __name__ == "__main__":
    main()
