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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth and auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return False, None
        
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

def test_custom_scenario_name():
    """Test the custom scenario name functionality"""
    print("\n" + "="*80)
    print("TESTING CUSTOM SCENARIO NAME FUNCTIONALITY")
    print("="*80)
    
    # Test setting a custom scenario with name
    scenario_data = {
        "scenario": "The world is facing a climate crisis. Global temperatures have risen by 2°C, causing extreme weather events, rising sea levels, and ecological disruption. World leaders are gathering for an emergency summit to address this existential threat.",
        "scenario_name": "Climate Crisis Summit"
    }
    
    set_scenario_test, set_scenario_response = run_test(
        "Set Custom Scenario with Name",
        "/simulation/set-scenario",
        method="POST",
        data=scenario_data,
        expected_keys=["message", "scenario", "scenario_name"]
    )
    
    if set_scenario_test and set_scenario_response:
        print(f"✅ Successfully set custom scenario with name: {set_scenario_response.get('scenario_name')}")
        
        # Verify the scenario name is returned correctly
        if set_scenario_response.get("scenario_name") == scenario_data["scenario_name"]:
            print("✅ Scenario name matches the input")
        else:
            print("❌ Scenario name does not match the input")
            set_scenario_test = False
    else:
        print("❌ Failed to set custom scenario with name")
    
    # Test setting a scenario without a name (should fail)
    invalid_scenario_data = {
        "scenario": "This is a test scenario without a name",
        "scenario_name": ""
    }
    
    invalid_scenario_test, invalid_scenario_response = run_test(
        "Set Scenario Without Name (Should Fail)",
        "/simulation/set-scenario",
        method="POST",
        data=invalid_scenario_data,
        expected_status=400
    )
    
    if invalid_scenario_test:
        print("✅ Correctly rejected scenario without a name")
    else:
        print("❌ Failed to reject scenario without a name")
    
    # Print summary
    print("\nCUSTOM SCENARIO NAME SUMMARY:")
    
    if set_scenario_test and invalid_scenario_test:
        print("✅ Custom scenario name functionality is working correctly!")
        print("✅ Scenario name is required and stored properly")
        print("✅ Scenario name validation works correctly")
        return True, "Custom scenario name functionality is working correctly"
    else:
        issues = []
        if not set_scenario_test:
            issues.append("Failed to set custom scenario with name")
        if not invalid_scenario_test:
            issues.append("Failed to reject scenario without a name")
        
        print("❌ Custom scenario name functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Custom scenario name functionality has issues"

def test_conversation_with_scenario_name():
    """Test that conversations include the scenario name"""
    print("\n" + "="*80)
    print("TESTING CONVERSATION WITH SCENARIO NAME")
    print("="*80)
    
    # Create test agents
    agents = []
    for i in range(2):
        agent_data = {
            "name": f"Climate Agent {i+1}",
            "archetype": "leader" if i == 0 else "scientist",
            "goal": "Address climate change through international cooperation",
            "expertise": "Environmental policy and climate science",
            "background": "PhD in Environmental Science with 15 years experience in climate policy"
        }
        
        agent_test, agent_response = run_test(
            f"Create Climate Test Agent {i+1}",
            "/agents",
            method="POST",
            data=agent_data,
            expected_keys=["id", "name"]
        )
        
        if agent_test and agent_response:
            agents.append(agent_response)
    
    if len(agents) < 2:
        print("❌ Failed to create enough test agents")
        return False, "Failed to create test agents"
    
    # Generate a conversation
    conversation_test, conversation_response = run_test(
        "Generate Conversation with Scenario Name",
        "/conversation/generate",
        method="POST",
        expected_keys=["messages", "round_number", "scenario"]
    )
    
    # Check if the conversation includes the scenario name
    scenario_name_included = False
    if conversation_test and conversation_response:
        if "scenario_name" in conversation_response:
            scenario_name = conversation_response.get("scenario_name", "")
            if scenario_name:
                scenario_name_included = True
                print(f"✅ Conversation includes scenario name: {scenario_name}")
            else:
                print("❌ Conversation scenario_name field is empty")
        else:
            print("❌ Conversation response does not include scenario_name field")
    else:
        print("❌ Failed to generate conversation")
    
    # Clean up - delete test agents
    for agent in agents:
        agent_id = agent.get("id")
        if agent_id:
            run_test(
                f"Delete Test Agent {agent_id}",
                f"/agents/{agent_id}",
                method="DELETE"
            )
    
    # Print summary
    print("\nCONVERSATION WITH SCENARIO NAME SUMMARY:")
    
    if conversation_test and scenario_name_included:
        print("✅ Conversations are properly tagged with scenario name!")
        return True, "Conversations are properly tagged with scenario name"
    else:
        issues = []
        if not conversation_test:
            issues.append("Failed to generate conversation")
        if not scenario_name_included:
            issues.append("Conversation does not include scenario name")
        
        print("❌ Conversation with scenario name has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Conversation with scenario name has issues"

def test_conversation_history_with_scenario_name():
    """Test that conversation history includes scenario name for organization"""
    print("\n" + "="*80)
    print("TESTING CONVERSATION HISTORY WITH SCENARIO NAME")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test conversation history without authentication")
            return False, "Authentication failed"
    
    # Create a test conversation to save
    conversation_data = {
        "simulation_id": str(uuid.uuid4()),
        "participants": ["Climate Scientist", "Policy Maker"],
        "messages": [
            {
                "agent_name": "Climate Scientist",
                "message": "Our data shows that we need immediate action to reduce carbon emissions."
            },
            {
                "agent_name": "Policy Maker",
                "message": "I agree. We should propose a carbon tax and increased investment in renewable energy."
            }
        ],
        "title": "Climate Policy Discussion",
        "scenario_name": "Climate Crisis Summit"  # Include scenario name
    }
    
    save_test, save_response = run_test(
        "Save Conversation with Scenario Name",
        "/conversation-history",
        method="POST",
        data=conversation_data,
        auth=True,
        expected_keys=["message"]
    )
    
    if save_test and save_response:
        print("✅ Successfully saved conversation with scenario name")
    else:
        print("❌ Failed to save conversation with scenario name")
    
    # Get conversation history
    history_test, history_response = run_test(
        "Get Conversation History",
        "/conversation-history",
        method="GET",
        auth=True
    )
    
    # Check if the conversation history includes the scenario name
    scenario_name_included = False
    if history_test and history_response:
        if isinstance(history_response, list) and len(history_response) > 0:
            for conversation in history_response:
                if "scenario_name" in conversation:
                    scenario_name = conversation.get("scenario_name", "")
                    if scenario_name:
                        scenario_name_included = True
                        print(f"✅ Conversation history includes scenario name: {scenario_name}")
                        break
            
            if not scenario_name_included:
                print("❌ No conversation in history includes scenario_name field")
        else:
            print("❌ Conversation history is empty or not a list")
    else:
        print("❌ Failed to retrieve conversation history")
    
    # Print summary
    print("\nCONVERSATION HISTORY WITH SCENARIO NAME SUMMARY:")
    
    if save_test and history_test and scenario_name_included:
        print("✅ Conversation history is properly organized by scenario name!")
        print("✅ Conversations can be saved with scenario name")
        print("✅ Conversation history includes scenario name field")
        return True, "Conversation history is properly organized by scenario name"
    else:
        issues = []
        if not save_test:
            issues.append("Failed to save conversation with scenario name")
        if not history_test:
            issues.append("Failed to retrieve conversation history")
        if not scenario_name_included:
            issues.append("Conversation history does not include scenario name")
        
        print("❌ Conversation history with scenario name has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Conversation history with scenario name has issues"

def test_documents_by_scenario():
    """Test that documents can be organized by scenario name"""
    print("\n" + "="*80)
    print("TESTING DOCUMENTS BY SCENARIO")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test documents by scenario without authentication")
            return False, "Authentication failed"
    
    # Create a test document with scenario name
    document_data = {
        "title": "Climate Crisis Action Plan",
        "category": "Protocol",
        "description": "A comprehensive plan to address the climate crisis",
        "content": "# Climate Crisis Action Plan\n\n## Purpose\nThis document outlines a comprehensive plan to address the global climate crisis through international cooperation and policy changes.\n\n## Key Actions\n1. Reduce carbon emissions by 50% by 2030\n2. Transition to renewable energy sources\n3. Implement carbon pricing mechanisms\n4. Protect and restore natural carbon sinks\n5. Develop climate-resilient infrastructure",
        "keywords": ["climate", "crisis", "action", "plan"],
        "authors": ["Climate Scientist", "Policy Maker"],
        "scenario_name": "Climate Crisis Summit"  # Include scenario name
    }
    
    create_test, create_response = run_test(
        "Create Document with Scenario Name",
        "/documents/create",
        method="POST",
        data=document_data,
        auth=True,
        expected_keys=["success", "document_id"]
    )
    
    document_id = None
    if create_test and create_response:
        document_id = create_response.get("document_id")
        print(f"✅ Successfully created document with ID: {document_id}")
    else:
        print("❌ Failed to create document with scenario name")
    
    # Get documents by scenario
    by_scenario_test, by_scenario_response = run_test(
        "Get Documents By Scenario",
        "/documents/by-scenario",
        method="GET",
        auth=True
    )
    
    # Check if the documents are organized by scenario name
    scenario_organization_works = False
    if by_scenario_test and by_scenario_response:
        if isinstance(by_scenario_response, list):
            for scenario in by_scenario_response:
                if scenario.get("scenario") == "Climate Crisis Summit":
                    scenario_organization_works = True
                    print(f"✅ Documents are organized by scenario name: {scenario.get('scenario')}")
                    print(f"✅ Found {scenario.get('document_count')} documents in this scenario")
                    break
            
            if not scenario_organization_works:
                print("❌ No documents found for 'Climate Crisis Summit' scenario")
        else:
            print("❌ Documents by scenario response is not a list")
    else:
        print("❌ Failed to retrieve documents by scenario")
    
    # Clean up - delete test document
    if document_id:
        delete_test, delete_response = run_test(
            "Delete Test Document",
            f"/documents/{document_id}",
            method="DELETE",
            auth=True,
            expected_keys=["success", "message"]
        )
        
        if delete_test and delete_response:
            print(f"✅ Deleted test document with ID: {document_id}")
        else:
            print(f"❌ Failed to delete test document with ID: {document_id}")
    
    # Print summary
    print("\nDOCUMENTS BY SCENARIO SUMMARY:")
    
    if create_test and by_scenario_test and scenario_organization_works:
        print("✅ Documents are properly organized by scenario name!")
        print("✅ Documents can be created with scenario name")
        print("✅ Documents can be retrieved by scenario name")
        return True, "Documents are properly organized by scenario name"
    else:
        issues = []
        if not create_test:
            issues.append("Failed to create document with scenario name")
        if not by_scenario_test:
            issues.append("Failed to retrieve documents by scenario")
        if not scenario_organization_works:
            issues.append("Documents are not organized by scenario name")
        
        print("❌ Documents by scenario has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Documents by scenario has issues"

def test_random_scenario_with_name():
    """Test that random scenarios include auto-generated names"""
    print("\n" + "="*80)
    print("TESTING RANDOM SCENARIO WITH AUTO-GENERATED NAME")
    print("="*80)
    
    # This test is more challenging to automate since we don't have a direct endpoint
    # to generate random scenarios on the backend. In a real application, we would
    # test this through the frontend or a specific API endpoint.
    
    # For this test, we'll check if the simulation state includes a scenario_name field
    # after setting a scenario, which indicates that the backend supports scenario names.
    
    # Get current simulation state
    state_test, state_response = run_test(
        "Get Simulation State",
        "/simulation/state",
        method="GET"
    )
    
    supports_scenario_name = False
    if state_test and state_response:
        if "scenario_name" in state_response:
            supports_scenario_name = True
            print(f"✅ Simulation state includes scenario_name field: {state_response.get('scenario_name')}")
        else:
            print("❌ Simulation state does not include scenario_name field")
    else:
        print("❌ Failed to retrieve simulation state")
    
    # Print summary
    print("\nRANDOM SCENARIO WITH AUTO-GENERATED NAME SUMMARY:")
    
    if supports_scenario_name:
        print("✅ Backend supports scenario names for random scenarios!")
        print("✅ Simulation state includes scenario_name field")
        return True, "Backend supports scenario names for random scenarios"
    else:
        print("❌ Backend may not fully support scenario names for random scenarios")
        print("Note: This test is limited since we can't directly test random scenario generation")
        return False, "Backend may not fully support scenario names for random scenarios"

def main():
    """Run all scenario name tests"""
    print("\n" + "="*80)
    print("RUNNING SCENARIO NAME FUNCTIONALITY TESTS")
    print("="*80)
    
    # Test authentication first
    test_login()
    
    # Run all scenario name tests
    custom_scenario_success, custom_scenario_message = test_custom_scenario_name()
    conversation_success, conversation_message = test_conversation_with_scenario_name()
    history_success, history_message = test_conversation_history_with_scenario_name()
    documents_success, documents_message = test_documents_by_scenario()
    random_scenario_success, random_scenario_message = test_random_scenario_with_name()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("SCENARIO NAME FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    all_tests_passed = (
        custom_scenario_success and 
        conversation_success and 
        history_success and 
        documents_success and 
        random_scenario_success
    )
    
    if all_tests_passed:
        print("✅ All scenario name functionality tests passed!")
        print("✅ Custom scenario name input works correctly")
        print("✅ Conversations are properly tagged with scenario name")
        print("✅ Conversation history is organized by scenario name")
        print("✅ Documents are organized by scenario name")
        print("✅ Backend supports scenario names for random scenarios")
    else:
        print("❌ Some scenario name functionality tests failed:")
        if not custom_scenario_success:
            print(f"  - {custom_scenario_message}")
        if not conversation_success:
            print(f"  - {conversation_message}")
        if not history_success:
            print(f"  - {history_message}")
        if not documents_success:
            print(f"  - {documents_message}")
        if not random_scenario_success:
            print(f"  - {random_scenario_message}")
    print("="*80)
    
    return all_tests_passed

if __name__ == "__main__":
    main()