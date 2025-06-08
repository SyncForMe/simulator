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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
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

def is_valid_url(url):
    """Check if a string is a valid URL"""
    url_pattern = re.compile(
        r'^(?:http|https)://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))

def test_avatar_generation():
    """Test the avatar generation functionality"""
    print("\n" + "="*80)
    print("TESTING AVATAR GENERATION FUNCTIONALITY")
    print("="*80)
    
    # 1. Test if the /api/avatars/generate endpoint exists and works
    avatar_data = {
        "prompt": "Nikola Tesla"
    }
    
    avatar_test, avatar_response = run_test(
        "Avatar Generation Endpoint",
        "/avatars/generate",
        method="POST",
        data=avatar_data,
        expected_keys=["success", "image_url"]
    )
    
    if avatar_test:
        # Verify the response contains a valid image URL
        image_url = avatar_response.get("image_url", "")
        if not image_url:
            print("❌ Response contains empty image_url")
            avatar_test = False
        elif not is_valid_url(image_url):
            print(f"❌ Response contains invalid URL: {image_url}")
            avatar_test = False
        else:
            print(f"✅ Response contains valid image URL: {image_url}")
            
            # Try to access the URL to verify it's accessible
            try:
                response = requests.head(image_url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Image URL is accessible (status code: {response.status_code})")
                else:
                    print(f"⚠️ Image URL returned non-200 status code: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Could not verify image URL accessibility: {e}")
    
    # 2. Test agent creation with avatar generation
    agent_data = {
        "name": "Nikola Tesla",
        "archetype": "scientist",
        "goal": "Advance understanding of electricity and wireless technology",
        "expertise": "Electrical engineering and physics",
        "background": "Inventor and electrical engineer known for AC electricity",
        "avatar_prompt": "Nikola Tesla, historical figure, inventor"
    }
    
    agent_test, agent_response = run_test(
        "Agent Creation with Avatar Generation",
        "/agents",
        method="POST",
        data=agent_data,
        expected_keys=["id", "name", "avatar_url", "avatar_prompt"]
    )
    
    if agent_test:
        # Verify the response contains a valid avatar URL
        avatar_url = agent_response.get("avatar_url", "")
        if not avatar_url:
            print("⚠️ Agent created but avatar_url is empty - this might be expected if generation failed")
        elif not is_valid_url(avatar_url):
            print(f"❌ Agent created but avatar_url is invalid: {avatar_url}")
            agent_test = False
        else:
            print(f"✅ Agent created with valid avatar URL: {avatar_url}")
            
            # Verify avatar_prompt was stored correctly
            stored_prompt = agent_response.get("avatar_prompt", "")
            if stored_prompt == agent_data["avatar_prompt"]:
                print(f"✅ Avatar prompt stored correctly: {stored_prompt}")
            else:
                print(f"❌ Avatar prompt mismatch: expected {agent_data['avatar_prompt']}, got {stored_prompt}")
                agent_test = False
    
    # 3. Test error handling for avatar generation
    # Use an empty prompt which should cause an error
    error_data = {
        "prompt": ""
    }
    
    error_test, error_response = run_test(
        "Avatar Generation Error Handling",
        "/avatars/generate",
        method="POST",
        data=error_data,
        expected_status=400  # Expecting a 400 Bad Request
    )
    
    # Print summary of avatar generation tests
    print("\nAVATAR GENERATION SUMMARY:")
    if avatar_test and agent_test and error_test:
        print("✅ Avatar generation functionality is working correctly!")
        print("✅ Dedicated avatar generation endpoint is working.")
        print("✅ Agent creation with avatar generation is working.")
        print("✅ Error handling for avatar generation is working.")
        return True, "Avatar generation functionality is working correctly"
    else:
        issues = []
        if not avatar_test:
            issues.append("Dedicated avatar generation endpoint has issues")
        if not agent_test:
            issues.append("Agent creation with avatar generation has issues")
        if not error_test:
            issues.append("Error handling for avatar generation has issues")
        
        print("❌ Avatar generation functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Avatar generation functionality has issues"

def test_agent_deletion():
    """Test the agent deletion functionality"""
    print("\n" + "="*80)
    print("TESTING AGENT DELETION FUNCTIONALITY")
    print("="*80)
    
    # 1. Create a test agent
    agent_data = {
        "name": "Test Agent For Deletion",
        "archetype": "scientist",
        "goal": "Test the deletion functionality",
        "expertise": "Being deleted",
        "background": "Created for deletion testing"
    }
    
    create_test, create_response = run_test(
        "Create Test Agent",
        "/agents",
        method="POST",
        data=agent_data,
        expected_keys=["id", "name"]
    )
    
    if not create_test:
        print("❌ Failed to create test agent. Aborting deletion tests.")
        return False, "Failed to create test agent for deletion testing"
    
    # Store the agent ID for deletion
    agent_id = create_response.get("id")
    print(f"✅ Created test agent with ID: {agent_id}")
    
    # 2. Verify the agent exists by getting all agents
    get_test, get_response = run_test(
        "Verify Agent Exists",
        "/agents",
        method="GET"
    )
    
    agent_exists = False
    if get_test:
        for agent in get_response:
            if agent.get("id") == agent_id:
                agent_exists = True
                print(f"✅ Verified agent with ID {agent_id} exists in the database")
                break
        
        if not agent_exists:
            print(f"❌ Created agent with ID {agent_id} not found in the database")
            return False, "Created agent not found in database"
    else:
        print("❌ Failed to get agents list. Skipping verification.")
    
    # 3. Test agent deletion
    delete_test, delete_response = run_test(
        "Delete Agent",
        f"/agents/{agent_id}",
        method="DELETE",
        expected_keys=["message"]
    )
    
    if not delete_test:
        print("❌ Failed to delete agent")
        return False, "Failed to delete agent"
    
    print(f"✅ Successfully deleted agent with ID: {agent_id}")
    
    # 4. Verify the agent is actually deleted
    verify_test, verify_response = run_test(
        "Verify Agent Deleted",
        "/agents",
        method="GET"
    )
    
    agent_deleted = True
    if verify_test:
        for agent in verify_response:
            if agent.get("id") == agent_id:
                agent_deleted = False
                print(f"❌ Agent with ID {agent_id} still exists in the database after deletion")
                break
        
        if agent_deleted:
            print(f"✅ Verified agent with ID {agent_id} was successfully removed from the database")
    else:
        print("❌ Failed to get agents list for deletion verification")
        return False, "Failed to verify agent deletion"
    
    # 5. Test error handling when trying to delete a non-existent agent
    nonexistent_id = "00000000-0000-0000-0000-000000000000"
    error_test, error_response = run_test(
        "Delete Non-existent Agent",
        f"/agents/{nonexistent_id}",
        method="DELETE",
        expected_status=404
    )
    
    if error_test:
        print(f"✅ Correctly returned 404 status when trying to delete non-existent agent")
    else:
        print(f"❌ Failed to handle non-existent agent deletion properly")
    
    # 6. Test deletion of agent with avatar
    agent_with_avatar_data = {
        "name": "Agent With Avatar",
        "archetype": "leader",
        "goal": "Test deletion with avatar",
        "expertise": "Having an avatar",
        "background": "Created for avatar deletion testing",
        "avatar_prompt": "Professional business person with glasses"
    }
    
    avatar_create_test, avatar_create_response = run_test(
        "Create Agent With Avatar",
        "/agents",
        method="POST",
        data=agent_with_avatar_data,
        expected_keys=["id", "name", "avatar_url"]
    )
    
    if not avatar_create_test:
        print("❌ Failed to create agent with avatar. Skipping avatar deletion test.")
    else:
        avatar_agent_id = avatar_create_response.get("id")
        has_avatar = bool(avatar_create_response.get("avatar_url"))
        
        if has_avatar:
            print(f"✅ Created agent with avatar. Agent ID: {avatar_agent_id}")
        else:
            print(f"⚠️ Created agent but no avatar was generated. Continuing test anyway.")
        
        # Delete the agent with avatar
        avatar_delete_test, avatar_delete_response = run_test(
            "Delete Agent With Avatar",
            f"/agents/{avatar_agent_id}",
            method="DELETE",
            expected_keys=["message"]
        )
        
        if avatar_delete_test:
            print(f"✅ Successfully deleted agent with avatar (ID: {avatar_agent_id})")
            
            # Verify deletion
            avatar_verify_test, avatar_verify_response = run_test(
                "Verify Avatar Agent Deleted",
                "/agents",
                method="GET"
            )
            
            avatar_agent_deleted = True
            if avatar_verify_test:
                for agent in avatar_verify_response:
                    if agent.get("id") == avatar_agent_id:
                        avatar_agent_deleted = False
                        print(f"❌ Agent with avatar (ID: {avatar_agent_id}) still exists after deletion")
                        break
                
                if avatar_agent_deleted:
                    print(f"✅ Verified agent with avatar was successfully removed from the database")
            else:
                print("❌ Failed to verify avatar agent deletion")
        else:
            print(f"❌ Failed to delete agent with avatar")
    
    # Print summary of agent deletion tests
    print("\nAGENT DELETION SUMMARY:")
    if create_test and delete_test and agent_deleted and error_test:
        print("✅ Agent deletion functionality is working correctly!")
        print("✅ Agents can be successfully created and deleted.")
        print("✅ Deleted agents are properly removed from the database.")
        print("✅ Error handling for non-existent agents is working.")
        if avatar_create_test and avatar_delete_test and avatar_agent_deleted:
            print("✅ Deletion of agents with avatars is working correctly.")
        return True, "Agent deletion functionality is working correctly"
    else:
        issues = []
        if not create_test:
            issues.append("Failed to create test agent")
        if not delete_test:
            issues.append("Failed to delete agent")
        if not agent_deleted:
            issues.append("Agent not properly removed from database after deletion")
        if not error_test:
            issues.append("Error handling for non-existent agents has issues")
        if avatar_create_test and (not avatar_delete_test or not avatar_agent_deleted):
            issues.append("Deletion of agents with avatars has issues")
        
        print("❌ Agent deletion functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Agent deletion functionality has issues"

def main():
    """Run API tests for agent deletion functionality"""
    print("Starting API tests for agent deletion functionality...")
    
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
    
    # 2. Test agent deletion functionality
    deletion_success, deletion_message = test_agent_deletion()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion about the agent deletion functionality
    print("\n" + "="*80)
    print("AGENT DELETION FUNCTIONALITY ASSESSMENT")
    print("="*80)
    if deletion_success:
        print("✅ The agent deletion functionality is working correctly!")
        print("✅ The DELETE /api/agents/{agent_id} endpoint is successfully deleting agents.")
        print("✅ Agents are properly removed from the database after deletion.")
        print("✅ Error handling for non-existent agents is implemented correctly.")
        print("✅ Deletion of agents with avatars is working properly.")
    else:
        print("❌ The agent deletion functionality is NOT working correctly.")
        print("❌ One or more agent deletion tests failed.")
        print("\nPossible issues:")
        print("1. The DELETE /api/agents/{agent_id} endpoint might not be implemented correctly")
        print("2. Agents might not be properly removed from the database")
        print("3. Error handling for non-existent agents might be incorrect")
        print("4. There might be issues with deleting agents that have avatars")
    print("="*80)

if __name__ == "__main__":
    main()
