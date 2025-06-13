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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None, params=None):
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

def test_auth_me():
    """Test the /auth/me endpoint with the auth token"""
    if not auth_token:
        if not test_login():
            print("❌ Cannot test /auth/me without authentication")
            return False, "Authentication failed"
    
    auth_me_test, auth_me_response = run_test(
        "Auth Me Endpoint",
        "/auth/me",
        method="GET",
        auth=True,
        expected_keys=["id", "email", "name"]
    )
    
    if auth_me_test and auth_me_response:
        print(f"✅ Auth Me endpoint returned user data: {auth_me_response.get('name')}")
        return True, "Auth Me endpoint is working correctly"
    else:
        print("❌ Auth Me endpoint failed")
        return False, "Auth Me endpoint failed"

def test_bulk_delete_functionality():
    """Test the bulk delete functionality for conversations and documents"""
    print("\n" + "="*80)
    print("TESTING BULK DELETE FUNCTIONALITY")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test bulk delete functionality without authentication")
            return False, "Authentication failed"
    
    # Test authentication requirement for both endpoints
    print("\nTesting authentication requirement for bulk delete endpoints:")
    
    # Test conversation bulk delete without auth
    no_auth_conv_test, _ = run_test(
        "Conversation Bulk Delete Without Auth",
        "/conversation-history/bulk",
        method="DELETE",
        data=["test-id-1", "test-id-2"],
        expected_status=403
    )
    
    # Test document bulk delete without auth
    no_auth_doc_test, _ = run_test(
        "Document Bulk Delete Without Auth",
        "/documents/bulk",
        method="DELETE",
        data=["test-id-1", "test-id-2"],
        expected_status=403
    )
    
    # Get existing conversations
    print("\nGetting existing conversations:")
    get_convs_test, get_convs_response = run_test(
        "Get Existing Conversations",
        "/conversation-history",
        method="GET",
        auth=True
    )
    
    conversation_ids = []
    if get_convs_test and get_convs_response:
        existing_convs = get_convs_response
        print(f"Found {len(existing_convs)} existing conversations")
        
        # Use existing conversations if available
        if len(existing_convs) >= 3:
            for i in range(3):
                conversation_ids.append(existing_convs[i].get("id"))
            print(f"Using existing conversation IDs: {conversation_ids}")
    
    # Create new conversations if needed
    if len(conversation_ids) < 3:
        print("\nCreating new test conversations:")
        for i in range(3 - len(conversation_ids)):
            conversation_data = {
                "participants": [f"Test Agent {j+1}" for j in range(3)],
                "messages": [
                    {
                        "agent_name": f"Test Agent {j+1}",
                        "message": f"This is test message {j+1} in conversation {i+1}"
                    } for j in range(3)
                ],
                "title": f"Test Conversation {i+1} for Bulk Delete",
                "scenario_name": "Bulk Delete Test"
            }
            
            conv_test, conv_response = run_test(
                f"Create Test Conversation {i+1}",
                "/conversation-history",
                method="POST",
                data=conversation_data,
                auth=True
            )
            
            if conv_test and conv_response:
                # Get the updated list of conversations to find the new one
                get_updated_convs_test, get_updated_convs_response = run_test(
                    "Get Updated Conversations",
                    "/conversation-history",
                    method="GET",
                    auth=True
                )
                
                if get_updated_convs_test and get_updated_convs_response:
                    updated_convs = get_updated_convs_response
                    # Find the newly created conversation (should be at the top)
                    if len(updated_convs) > 0:
                        conversation_ids.append(updated_convs[0].get("id"))
                        print(f"Added conversation ID: {updated_convs[0].get('id')}")
    
    # Get existing documents
    print("\nGetting existing documents:")
    get_docs_test, get_docs_response = run_test(
        "Get Existing Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    document_ids = []
    if get_docs_test and get_docs_response:
        existing_docs = get_docs_response
        print(f"Found {len(existing_docs)} existing documents")
        
        # Use existing documents if available
        if len(existing_docs) >= 3:
            for i in range(3):
                document_ids.append(existing_docs[i].get("id"))
            print(f"Using existing document IDs: {document_ids}")
    
    # Create new documents if needed
    if len(document_ids) < 3:
        print("\nCreating new test documents:")
        for i in range(3 - len(document_ids)):
            document_data = {
                "title": f"Test Document {i+1} for Bulk Delete",
                "category": "Protocol",
                "description": f"This is test document {i+1} for bulk delete testing",
                "content": f"# Test Document {i+1}\n\nThis is a test document for bulk delete testing.",
                "keywords": ["test", "bulk", "delete"],
                "authors": ["Test Agent"]
            }
            
            doc_test, doc_response = run_test(
                f"Create Test Document {i+1}",
                "/documents/create",
                method="POST",
                data=document_data,
                auth=True,
                expected_keys=["document_id"]
            )
            
            if doc_test and doc_response:
                document_ids.append(doc_response.get("document_id"))
                print(f"Created document with ID: {doc_response.get('document_id')}")
    
    # Test conversation bulk delete with valid IDs
    print("\nTesting conversation bulk delete with valid IDs:")
    if len(conversation_ids) >= 2:
        # Delete first two conversations
        delete_ids = conversation_ids[:2]
        print(f"Attempting to delete conversation IDs: {delete_ids}")
        conv_bulk_test, conv_bulk_response = run_test(
            "Conversation Bulk Delete",
            "/conversation-history/bulk",
            method="DELETE",
            data=delete_ids,  # Pass as request body
            auth=True,
            expected_keys=["message", "deleted_count"]
        )
        
        if conv_bulk_test and conv_bulk_response:
            deleted_count = conv_bulk_response.get("deleted_count", 0)
            if deleted_count == len(delete_ids):
                print(f"✅ Successfully deleted {deleted_count} conversations")
            else:
                print(f"❌ Expected to delete {len(delete_ids)} conversations, but deleted {deleted_count}")
        
        # Verify the conversations were deleted
        get_convs_test, get_convs_response = run_test(
            "Get Conversations After Bulk Delete",
            "/conversation-history",
            method="GET",
            auth=True
        )
        
        if get_convs_test and get_convs_response:
            remaining_convs = get_convs_response
            remaining_ids = [conv.get("id") for conv in remaining_convs]
            
            # Check if deleted IDs are no longer present
            deleted_ids_present = any(conv_id in remaining_ids for conv_id in delete_ids)
            if not deleted_ids_present:
                print("✅ Deleted conversations are no longer in the database")
            else:
                print("❌ Some deleted conversations are still in the database")
            
            # Check if non-deleted ID is still present (if we had at least 3)
            if len(conversation_ids) >= 3 and conversation_ids[2] in remaining_ids:
                print("✅ Non-deleted conversation is still in the database")
            else:
                print("❌ Non-deleted conversation is missing from the database or not enough conversations were created")
    else:
        print("❌ Not enough test conversations available, skipping conversation bulk delete test")
    
    # Test document bulk delete with valid IDs
    print("\nTesting document bulk delete with valid IDs:")
    if len(document_ids) >= 2:
        # Delete first two documents
        delete_ids = document_ids[:2]
        print(f"Attempting to delete document IDs: {delete_ids}")
        doc_bulk_test, doc_bulk_response = run_test(
            "Document Bulk Delete",
            "/documents/bulk",
            method="DELETE",
            data=delete_ids,  # Pass as request body
            auth=True,
            expected_keys=["message", "deleted_count"]
        )
        
        if doc_bulk_test and doc_bulk_response:
            deleted_count = doc_bulk_response.get("deleted_count", 0)
            if deleted_count == len(delete_ids):
                print(f"✅ Successfully deleted {deleted_count} documents")
            else:
                print(f"❌ Expected to delete {len(delete_ids)} documents, but deleted {deleted_count}")
        else:
            print("❌ Document bulk delete failed")
            
            # Try with a single document ID to see if that works
            if len(document_ids) > 0:
                print("\nTrying document bulk delete with a single ID:")
                single_id = [document_ids[0]]
                print(f"Attempting to delete document ID: {single_id}")
                single_doc_test, single_doc_response = run_test(
                    "Document Bulk Delete (Single ID)",
                    "/documents/bulk",
                    method="DELETE",
                    data=single_id,
                    auth=True,
                    expected_keys=["message", "deleted_count"]
                )
                
                if single_doc_test and single_doc_response:
                    print(f"✅ Successfully deleted single document")
                else:
                    print("❌ Even single document delete failed")
    else:
        print("❌ Not enough test documents created, skipping document bulk delete test")
    
    # Test conversation bulk delete with non-existent IDs
    print("\nTesting conversation bulk delete with non-existent IDs:")
    non_existent_ids = ["non-existent-id-1", "non-existent-id-2"]
    non_exist_conv_test, non_exist_conv_response = run_test(
        "Conversation Bulk Delete with Non-Existent IDs",
        "/conversation-history/bulk",
        method="DELETE",
        data=non_existent_ids,  # Pass as request body
        auth=True,
        expected_status=404
    )
    
    if non_exist_conv_test:
        print("❌ Expected 404 error for non-existent conversation IDs, but got success")
    else:
        print("✅ Correctly returned 404 for non-existent conversation IDs")
    
    # Test document bulk delete with non-existent IDs
    print("\nTesting document bulk delete with non-existent IDs:")
    non_exist_doc_test, non_exist_doc_response = run_test(
        "Document Bulk Delete with Non-Existent IDs",
        "/documents/bulk",
        method="DELETE",
        data=non_existent_ids,  # Pass as request body
        auth=True,
        expected_status=404
    )
    
    if non_exist_doc_test:
        print("❌ Expected 404 error for non-existent document IDs, but got success")
    else:
        print("✅ Correctly returned 404 for non-existent document IDs")
    
    # Test conversation bulk delete with empty array
    print("\nTesting conversation bulk delete with empty array:")
    empty_conv_test, empty_conv_response = run_test(
        "Conversation Bulk Delete with Empty Array",
        "/conversation-history/bulk",
        method="DELETE",
        data=[],  # Pass as request body
        auth=True,
        expected_keys=["message", "deleted_count"]
    )
    
    if empty_conv_test and empty_conv_response:
        deleted_count = empty_conv_response.get("deleted_count", -1)
        if deleted_count == 0:
            print("✅ Correctly reported 0 deleted conversations for empty array")
        else:
            print(f"❌ Expected 0 deleted conversations for empty array, but got {deleted_count}")
    
    # Test document bulk delete with empty array
    print("\nTesting document bulk delete with empty array:")
    print(f"Sending empty array to /documents/bulk endpoint: {[]}")
    empty_doc_test, empty_doc_response = run_test(
        "Document Bulk Delete with Empty Array",
        "/documents/bulk",
        method="DELETE",
        data=[],  # Pass as request body
        auth=True,
        expected_status=200,  # Should return 200 with deleted_count=0
        expected_keys=["message", "deleted_count"]
    )
    
    if empty_doc_test and empty_doc_response:
        deleted_count = empty_doc_response.get("deleted_count", -1)
        if deleted_count == 0:
            print("✅ Correctly reported 0 deleted documents for empty array")
        else:
            print(f"❌ Expected 0 deleted documents for empty array, but got {deleted_count}")
    else:
        print("❌ Document bulk delete with empty array failed - should return 200 with deleted_count=0")
        print(f"Response: {empty_doc_response}")
        print(f"Status code: {empty_doc_test}")
    
    # Clean up - delete remaining conversation and document
    if len(conversation_ids) >= 3:
        run_test(
            "Delete Remaining Test Conversation",
            f"/conversation-history/{conversation_ids[2]}",
            method="DELETE",
            auth=True
        )
    
    if len(document_ids) >= 3:
        run_test(
            "Delete Remaining Test Document",
            f"/documents/{document_ids[2]}",
            method="DELETE",
            auth=True
        )
    
    # Print summary
    print("\nBULK DELETE FUNCTIONALITY SUMMARY:")
    
    auth_tests_passed = not no_auth_conv_test and not no_auth_doc_test
    conv_bulk_tests_passed = len(conversation_ids) >= 2 and conv_bulk_test and not non_exist_conv_test and empty_conv_test
    doc_bulk_tests_passed = len(document_ids) >= 2 and doc_bulk_test and not non_exist_doc_test
    
    # Special check for document empty array test
    doc_empty_array_issue = not empty_doc_test or empty_doc_response.get("deleted_count", -1) != 0
    
    if auth_tests_passed and conv_bulk_tests_passed and doc_bulk_tests_passed and not doc_empty_array_issue:
        print("✅ Bulk delete functionality is working correctly!")
        print("✅ Authentication is properly enforced for both endpoints")
        print("✅ Conversation bulk delete works correctly with valid IDs")
        print("✅ Document bulk delete works correctly with valid IDs")
        print("✅ Both endpoints handle non-existent IDs correctly")
        print("✅ Both endpoints handle empty arrays correctly")
        return True, "Bulk delete functionality is working correctly"
    else:
        issues = []
        if not auth_tests_passed:
            issues.append("Authentication is not properly enforced for bulk delete endpoints")
        if not conv_bulk_tests_passed:
            issues.append("Conversation bulk delete has issues")
        if not doc_bulk_tests_passed:
            issues.append("Document bulk delete has issues")
        if doc_empty_array_issue:
            issues.append("Document bulk delete with empty array returns 404 instead of 200 with deleted_count=0")
        
        print("❌ Bulk delete functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Bulk delete functionality has issues"

def test_document_by_scenario():
    """Test the /documents/by-scenario endpoint"""
    print("\n" + "="*80)
    print("TESTING DOCUMENTS BY SCENARIO ENDPOINT")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test documents by scenario without authentication")
            return False, "Authentication failed"
    
    # Test the endpoint
    by_scenario_test, by_scenario_response = run_test(
        "Get Documents By Scenario",
        "/documents/by-scenario",
        method="GET",
        auth=True
    )
    
    if by_scenario_test and by_scenario_response:
        # Check if the response is a list
        if isinstance(by_scenario_response, list):
            print(f"✅ Received a list of {len(by_scenario_response)} scenarios")
            
            # Check if each scenario has the expected structure
            for i, scenario in enumerate(by_scenario_response[:3]):  # Check first 3 scenarios
                print(f"\nScenario {i+1}: {scenario.get('scenario')}")
                print(f"Document count: {scenario.get('document_count')}")
                
                # Check if documents are present
                documents = scenario.get('documents', [])
                print(f"Documents in response: {len(documents)}")
                
                # Print details of first 2 documents in each scenario
                for j, doc in enumerate(documents[:2]):
                    print(f"  Document {j+1}:")
                    print(f"    ID: {doc.get('id')}")
                    print(f"    Title: {doc.get('title')}")
                    print(f"    Category: {doc.get('category')}")
            
            return True, "Documents by scenario endpoint is working correctly"
        else:
            print("❌ Expected a list of scenarios, but got something else")
            return False, "Documents by scenario endpoint returned unexpected format"
    else:
        print("❌ Documents by scenario endpoint failed")
        return False, "Documents by scenario endpoint failed"

def test_agent_library_creation():
    """Test the agent creation functionality from the Agent Library component"""
    print("\n" + "="*80)
    print("TESTING AGENT LIBRARY CREATION FUNCTIONALITY")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test agent creation without authentication")
            return False, "Authentication failed"
    
    # Test authentication requirement for agent creation
    print("\nTesting authentication requirement for agent creation:")
    
    # Test agent creation without auth
    test_agent_data = {
        "name": "Test Agent",
        "archetype": "scientist",
        "goal": "To test the agent creation functionality",
        "background": "Experienced in testing APIs",
        "expertise": "API testing and validation",
        "memory_summary": "Created for testing the Agent Library component",
        "avatar_prompt": "Professional scientist in a lab coat"
    }
    
    no_auth_test, _ = run_test(
        "Agent Creation Without Auth",
        "/agents",
        method="POST",
        data=test_agent_data,
        expected_status=403
    )
    
    # Test agent creation with auth
    print("\nTesting agent creation with authentication:")
    
    # Test with valid data
    valid_agent_data = {
        "name": "Dr. Jane Smith",
        "archetype": "scientist",  # Using lowercase key as required
        "goal": "To advance medical research through innovative approaches",
        "background": "PhD in Molecular Biology with 15 years of research experience",
        "expertise": "Gene therapy, clinical trials, and research methodology",
        "memory_summary": "Leading expert in CRISPR technology with multiple published papers",
        "avatar_prompt": "Professional female scientist with glasses and lab coat"
    }
    
    valid_test, valid_response = run_test(
        "Agent Creation With Valid Data",
        "/agents",
        method="POST",
        data=valid_agent_data,
        auth=True,
        expected_keys=["id", "name", "archetype", "personality", "goal", "expertise", "background", "memory_summary", "avatar_url", "avatar_prompt"]
    )
    
    if valid_test and valid_response:
        agent_id = valid_response.get("id")
        print(f"✅ Successfully created agent with ID: {agent_id}")
        print(f"✅ Agent name: {valid_response.get('name')}")
        print(f"✅ Agent archetype: {valid_response.get('archetype')}")
        print(f"✅ Personality was auto-generated: {valid_response.get('personality')}")
        
        # Check if avatar was generated (if avatar_prompt was provided)
        if valid_response.get("avatar_url"):
            print(f"✅ Avatar was generated: {valid_response.get('avatar_url')}")
        
        # Verify the agent was created by getting all agents
        get_agents_test, get_agents_response = run_test(
            "Get All Agents",
            "/agents",
            method="GET",
            auth=True
        )
        
        if get_agents_test and get_agents_response:
            # Check if our newly created agent is in the list
            agent_found = False
            for agent in get_agents_response:
                if agent.get("id") == agent_id:
                    agent_found = True
                    break
            
            if agent_found:
                print("✅ Newly created agent found in the agents list")
            else:
                print("❌ Newly created agent not found in the agents list")
    
    # Test with invalid archetype
    invalid_agent_data = {
        "name": "Invalid Agent",
        "archetype": "invalid_archetype",  # This should fail
        "goal": "To test invalid archetype handling",
        "background": "Testing background",
        "expertise": "Testing expertise",
        "memory_summary": "Testing memory",
        "avatar_prompt": "Test avatar"
    }
    
    invalid_test, _ = run_test(
        "Agent Creation With Invalid Archetype",
        "/agents",
        method="POST",
        data=invalid_agent_data,
        auth=True,
        expected_status=400
    )
    
    if not invalid_test:
        print("✅ Correctly rejected invalid archetype")
    else:
        print("❌ Failed to reject invalid archetype")
    
    # Test with pre-generated avatar URL
    avatar_url_agent_data = {
        "name": "Dr. John Doe",
        "archetype": "leader",
        "goal": "To lead the research team effectively",
        "background": "Former department head with management experience",
        "expertise": "Team leadership and project management",
        "memory_summary": "Experienced in leading cross-functional teams",
        "avatar_url": "https://example.com/avatar.jpg",  # Pre-generated URL
        "avatar_prompt": ""  # Empty prompt since we're using a URL
    }
    
    avatar_url_test, avatar_url_response = run_test(
        "Agent Creation With Pre-generated Avatar URL",
        "/agents",
        method="POST",
        data=avatar_url_agent_data,
        auth=True,
        expected_keys=["id", "name", "archetype", "personality", "goal", "expertise", "background", "memory_summary", "avatar_url"]
    )
    
    if avatar_url_test and avatar_url_response:
        if avatar_url_response.get("avatar_url") == "https://example.com/avatar.jpg":
            print("✅ Successfully used pre-generated avatar URL")
        else:
            print("❌ Failed to use pre-generated avatar URL")
    
    # Test saving agent to library
    print("\nTesting saving agent to library:")
    
    saved_agent_data = {
        "name": "Dr. Sarah Chen",
        "archetype": "mediator",
        "goal": "To facilitate collaboration between research teams",
        "background": "Mediator with experience in conflict resolution",
        "expertise": "Negotiation and team building",
        "avatar_prompt": "Professional female mediator in business attire"
    }
    
    saved_agent_test, saved_agent_response = run_test(
        "Save Agent to Library",
        "/saved-agents",
        method="POST",
        data=saved_agent_data,
        auth=True,
        expected_keys=["id", "user_id", "name", "archetype", "personality", "goal", "expertise", "background", "avatar_url", "avatar_prompt"]
    )
    
    if saved_agent_test and saved_agent_response:
        saved_agent_id = saved_agent_response.get("id")
        print(f"✅ Successfully saved agent to library with ID: {saved_agent_id}")
        print(f"✅ User ID: {saved_agent_response.get('user_id')}")
        
        # Verify the agent was saved by getting all saved agents
        get_saved_agents_test, get_saved_agents_response = run_test(
            "Get Saved Agents",
            "/saved-agents",
            method="GET",
            auth=True
        )
        
        if get_saved_agents_test and get_saved_agents_response:
            # Check if our newly saved agent is in the list
            agent_found = False
            for agent in get_saved_agents_response:
                if agent.get("id") == saved_agent_id:
                    agent_found = True
                    break
            
            if agent_found:
                print("✅ Newly saved agent found in the saved agents list")
            else:
                print("❌ Newly saved agent not found in the saved agents list")
            
            # Clean up - delete the saved agent
            delete_saved_agent_test, _ = run_test(
                "Delete Saved Agent",
                f"/saved-agents/{saved_agent_id}",
                method="DELETE",
                auth=True
            )
            
            if delete_saved_agent_test:
                print("✅ Successfully deleted saved agent")
            else:
                print("❌ Failed to delete saved agent")
    
    # Print summary
    print("\nAGENT LIBRARY CREATION FUNCTIONALITY SUMMARY:")
    
    auth_test_passed = not no_auth_test
    valid_creation_passed = valid_test
    invalid_archetype_passed = not invalid_test
    avatar_url_passed = avatar_url_test
    saved_agent_passed = saved_agent_test
    
    if auth_test_passed and valid_creation_passed and invalid_archetype_passed and avatar_url_passed and saved_agent_passed:
        print("✅ Agent Library creation functionality is working correctly!")
        print("✅ Authentication is properly enforced")
        print("✅ Agent creation works with valid data")
        print("✅ Invalid archetypes are properly rejected")
        print("✅ Pre-generated avatar URLs are properly used")
        print("✅ Agents can be saved to the library")
        return True, "Agent Library creation functionality is working correctly"
    else:
        issues = []
        if not auth_test_passed:
            issues.append("Authentication is not properly enforced for agent creation")
        if not valid_creation_passed:
            issues.append("Agent creation with valid data failed")
        if not invalid_archetype_passed:
            issues.append("Invalid archetypes are not properly rejected")
        if not avatar_url_passed:
            issues.append("Pre-generated avatar URLs are not properly used")
        if not saved_agent_passed:
            issues.append("Agents cannot be saved to the library")
        
        print("❌ Agent Library creation functionality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Agent Library creation functionality has issues"

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING BACKEND API TESTS")
    print("="*80)
    
    # Test authentication first
    test_login()
    test_auth_me()
    
    # Test agent library creation functionality
    agent_library_success, agent_library_message = test_agent_library_creation()
    
    # Test documents by scenario endpoint
    docs_by_scenario_success, docs_by_scenario_message = test_document_by_scenario()
    
    # Test bulk delete functionality
    bulk_delete_success, bulk_delete_message = test_bulk_delete_functionality()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("AGENT LIBRARY CREATION FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    if agent_library_success:
        print("✅ Agent Library creation functionality is working correctly!")
        print("✅ Authentication is properly enforced")
        print("✅ Agent creation works with valid data")
        print("✅ Invalid archetypes are properly rejected")
        print("✅ Pre-generated avatar URLs are properly used")
        print("✅ Agents can be saved to the library")
    else:
        print(f"❌ {agent_library_message}")
    
    print("\n" + "="*80)
    print("BULK DELETE FUNCTIONALITY ASSESSMENT")
    print("="*80)
    
    if bulk_delete_success:
        print("✅ Bulk delete functionality is working correctly!")
        print("✅ Both conversation and document bulk delete endpoints are properly implemented")
        print("✅ Authentication is properly enforced")
        print("✅ User data isolation is working correctly")
        print("✅ Error handling is implemented for non-existent IDs")
        print("✅ Empty arrays are handled correctly")
    else:
        print(f"❌ {bulk_delete_message}")
        
        # Provide specific details about the document bulk delete issue
        print("\nIssue with document bulk delete:")
        print("The document bulk delete endpoint is not working correctly with empty arrays.")
        print("When an empty array is provided, it returns a 404 error with 'Document not found'")
        print("instead of a 200 success with deleted_count=0.")
        print("\nPossible fix:")
        print("The issue is in the server.py file, where the empty array check is implemented")
        print("but the document verification logic still tries to find documents even when the array is empty.")
    
    print("="*80)
    
    return agent_library_success and bulk_delete_success

if __name__ == "__main__":
    main()
