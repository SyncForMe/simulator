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

def test_document_categories():
    """Test the document categories endpoint"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT CATEGORIES ENDPOINT")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document categories without authentication")
            return False, "Authentication failed"
    
    # Test GET /api/documents/categories
    categories_test, categories_response = run_test(
        "Document Categories",
        "/documents/categories",
        method="GET",
        auth=True,  # Add authentication
        expected_keys=["categories"]
    )
    
    # Verify the expected categories are present
    expected_categories = ["Protocol", "Training", "Research", "Equipment", "Budget", "Reference"]
    categories_valid = False
    
    if categories_test and categories_response:
        categories = categories_response.get("categories", [])
        missing_categories = [cat for cat in expected_categories if cat not in categories]
        
        if not missing_categories:
            categories_valid = True
            print("✅ All expected categories are present")
        else:
            print(f"❌ Missing categories: {missing_categories}")
    
    # Print summary
    print("\nDOCUMENT CATEGORIES ENDPOINT SUMMARY:")
    
    if categories_test and categories_valid:
        print("✅ Document categories endpoint is working correctly!")
        print("✅ Returns all expected categories: Protocol, Training, Research, Equipment, Budget, Reference")
        return True, "Document categories endpoint is working correctly"
    else:
        issues = []
        if not categories_test:
            issues.append("Document categories endpoint request failed")
        if not categories_valid:
            issues.append("Document categories response is missing expected categories")
        
        print("❌ Document categories endpoint has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Document categories endpoint has issues"

def test_action_trigger_analysis():
    """Test the conversation analysis functionality"""
    print("\n" + "="*80)
    print("TESTING ACTION TRIGGER ANALYSIS")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test action trigger analysis without authentication")
            return False, "Authentication failed"
    
    # Create test conversation with trigger phrases
    conversation_text = """
    Dr. Smith: I've been thinking about our emergency procedures. They're outdated and don't cover the new equipment.
    Dr. Johnson: You're right. We need a protocol for emergency procedures, especially for the new MRI machine.
    Dr. Williams: I agree. The current procedures are insufficient. Let's create a comprehensive protocol.
    Dr. Brown: Absolutely. I can help draft it. We should include evacuation routes and emergency contacts.
    Dr. Smith: Great idea. We'll need to train everyone on the new protocol once it's ready.
    """
    
    # Create test agents for the conversation
    agents = []
    for i in range(2):
        agent_data = {
            "name": f"Dr. Test {i+1}",
            "archetype": "scientist",
            "goal": "Test action trigger analysis",
            "expertise": "Testing"
        }
        
        agent_test, agent_response = run_test(
            f"Create Test Agent {i+1} for Action Trigger Analysis",
            "/agents",
            method="POST",
            data=agent_data,
            expected_keys=["id", "name"]
        )
        
        if agent_test and agent_response:
            agents.append(agent_response)
    
    # Test the conversation analysis endpoint
    analysis_data = {
        "conversation_text": conversation_text,
        "agent_ids": [agent.get("id") for agent in agents]  # Use created agent IDs
    }
    
    analysis_test, analysis_response = run_test(
        "Action Trigger Analysis",
        "/documents/analyze-conversation",
        method="POST",
        data=analysis_data,
        auth=True,
        expected_keys=["should_create_document"]
    )
    
    # Verify the analysis detected the trigger
    trigger_detected = False
    if analysis_test and analysis_response:
        should_create = analysis_response.get("should_create_document", False)
        document_type = analysis_response.get("document_type", "")
        document_title = analysis_response.get("document_title", "")
        trigger_phrase = analysis_response.get("trigger_phrase", "")
        
        trigger_detected = should_create and document_type and document_title and trigger_phrase
        
        if trigger_detected:
            print(f"✅ Trigger detected: {trigger_phrase}")
            print(f"✅ Document type: {document_type}")
            print(f"✅ Document title: {document_title}")
        else:
            print("❌ Trigger not detected or missing information")
    
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
    print("\nACTION TRIGGER ANALYSIS SUMMARY:")
    
    if analysis_test and trigger_detected:
        print("✅ Action trigger analysis is working correctly!")
        print("✅ Successfully detected trigger phrase in conversation")
        print("✅ Correctly identified document type and title")
        return True, "Action trigger analysis is working correctly"
    else:
        issues = []
        if not analysis_test:
            issues.append("Action trigger analysis request failed")
        if not trigger_detected:
            issues.append("Action trigger not detected in conversation with clear trigger phrase")
        
        print("❌ Action trigger analysis has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Action trigger analysis has issues"

def test_document_generation():
    """Test the document generation endpoint"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT GENERATION")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document generation without authentication")
            return False, "Authentication failed"
    
    # Test data for document generation
    document_data = {
        "document_type": "protocol",
        "title": "Emergency Procedures Protocol",
        "conversation_context": """
        Dr. Smith: I've been thinking about our emergency procedures. They're outdated and don't cover the new equipment.
        Dr. Johnson: You're right. We need a protocol for emergency procedures, especially for the new MRI machine.
        Dr. Williams: I agree. The current procedures are insufficient. Let's create a comprehensive protocol.
        Dr. Brown: Absolutely. I can help draft it. We should include evacuation routes and emergency contacts.
        Dr. Smith: Great idea. We'll need to train everyone on the new protocol once it's ready.
        """,
        "creating_agent_id": "test-agent-id",  # This might not exist, but the endpoint should handle it
        "authors": ["Dr. Smith", "Dr. Johnson", "Dr. Williams", "Dr. Brown"],
        "trigger_phrase": "We need a protocol for emergency procedures"
    }
    
    # Create a test agent first to get a valid agent ID
    agent_data = {
        "name": "Dr. Test",
        "archetype": "scientist",
        "goal": "Test document generation",
        "expertise": "Testing"
    }
    
    agent_test, agent_response = run_test(
        "Create Test Agent for Document Generation",
        "/agents",
        method="POST",
        data=agent_data,
        expected_keys=["id", "name"]
    )
    
    if agent_test and agent_response:
        # Update document data with valid agent ID
        document_data["creating_agent_id"] = agent_response.get("id")
    
    # Test document generation
    generation_test, generation_response = run_test(
        "Document Generation",
        "/documents/generate",
        method="POST",
        data=document_data,
        auth=True,
        expected_keys=["success", "document_id", "content"]
    )
    
    # Verify document was generated with proper content
    document_valid = False
    if generation_test and generation_response:
        success = generation_response.get("success", False)
        document_id = generation_response.get("document_id", "")
        content = generation_response.get("content", "")
        
        # Check if content has expected sections for a protocol
        has_purpose = "Purpose" in content
        has_scope = "Scope" in content
        has_procedure = "Procedure" in content
        
        document_valid = success and document_id and content and has_purpose and has_scope and has_procedure
        
        if document_valid:
            print(f"✅ Document generated successfully with ID: {document_id}")
            print(f"✅ Document has proper structure with Purpose, Scope, and Procedure sections")
        else:
            print("❌ Document generation failed or document has invalid structure")
            if not has_purpose:
                print("  - Missing Purpose section")
            if not has_scope:
                print("  - Missing Scope section")
            if not has_procedure:
                print("  - Missing Procedure section")
    
    # Print summary
    print("\nDOCUMENT GENERATION SUMMARY:")
    
    if generation_test and document_valid:
        print("✅ Document generation is working correctly!")
        print("✅ Successfully generated document with proper structure")
        print("✅ Document includes required metadata and content")
        return True, "Document generation is working correctly"
    else:
        issues = []
        if not generation_test:
            issues.append("Document generation request failed")
        if not document_valid:
            issues.append("Generated document has invalid structure or missing content")
        
        print("❌ Document generation has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Document generation has issues"

def test_file_center_integration():
    """Test the File Center API endpoints"""
    print("\n" + "="*80)
    print("TESTING FILE CENTER INTEGRATION")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test File Center integration without authentication")
            return False, "Authentication failed"
    
    # 1. Create a document
    document_data = {
        "title": "Test Protocol Document",
        "category": "Protocol",
        "description": "A test protocol document for API testing",
        "content": """# Test Protocol Document

## Purpose
This is a test protocol document created for API testing.

## Scope
This protocol applies to all test scenarios.

## Procedure
1. Step 1: Do something
2. Step 2: Do something else
3. Step 3: Verify results
""",
        "keywords": ["test", "protocol", "api"],
        "authors": ["Test User"]
    }
    
    create_test, create_response = run_test(
        "Create Document in File Center",
        "/documents/create",
        method="POST",
        data=document_data,
        auth=True,
        expected_keys=["success", "document_id"]
    )
    
    document_id = None
    if create_test and create_response:
        document_id = create_response.get("document_id")
        print(f"✅ Document created with ID: {document_id}")
    else:
        print("❌ Document creation failed")
    
    # 2. Retrieve all documents
    retrieve_all_test, retrieve_all_response = run_test(
        "Retrieve All Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    documents_retrievable = False
    if retrieve_all_test and retrieve_all_response:
        if isinstance(retrieve_all_response, list):
            documents_retrievable = True
            print(f"✅ Retrieved {len(retrieve_all_response)} documents")
        else:
            print("❌ Document retrieval failed - response is not a list")
    
    # 3. Retrieve document by ID
    retrieve_by_id_test = False
    if document_id:
        retrieve_by_id_test, retrieve_by_id_response = run_test(
            "Retrieve Document by ID",
            f"/documents/{document_id}",
            method="GET",
            auth=True,
            expected_keys=["id", "metadata", "content"]
        )
        
        if retrieve_by_id_test:
            print(f"✅ Retrieved document by ID: {document_id}")
        else:
            print(f"❌ Failed to retrieve document by ID: {document_id}")
    
    # 4. Search and filter documents
    search_test, search_response = run_test(
        "Search Documents",
        "/documents?search=test",
        method="GET",
        auth=True
    )
    
    search_works = False
    if search_test and search_response:
        if isinstance(search_response, list):
            search_works = True
            print(f"✅ Search returned {len(search_response)} documents")
        else:
            print("❌ Document search failed - response is not a list")
    
    # 5. Filter documents by category
    filter_test, filter_response = run_test(
        "Filter Documents by Category",
        "/documents?category=Protocol",
        method="GET",
        auth=True
    )
    
    filter_works = False
    if filter_test and filter_response:
        if isinstance(filter_response, list):
            filter_works = True
            print(f"✅ Category filter returned {len(filter_response)} documents")
        else:
            print("❌ Document category filtering failed - response is not a list")
    
    # 6. Delete document
    delete_test = False
    if document_id:
        delete_test, delete_response = run_test(
            "Delete Document",
            f"/documents/{document_id}",
            method="DELETE",
            auth=True,
            expected_keys=["success", "message"]
        )
        
        if delete_test:
            print(f"✅ Deleted document with ID: {document_id}")
        else:
            print(f"❌ Failed to delete document with ID: {document_id}")
    
    # Print summary
    print("\nFILE CENTER INTEGRATION SUMMARY:")
    
    all_tests_passed = create_test and documents_retrievable and search_works and filter_works
    if document_id:
        all_tests_passed = all_tests_passed and retrieve_by_id_test and delete_test
    
    if all_tests_passed:
        print("✅ File Center integration is working correctly!")
        print("✅ Documents can be created, retrieved, searched, filtered, and deleted")
        return True, "File Center integration is working correctly"
    else:
        issues = []
        if not create_test:
            issues.append("Document creation failed")
        if not documents_retrievable:
            issues.append("Document retrieval failed")
        if document_id and not retrieve_by_id_test:
            issues.append("Document retrieval by ID failed")
        if not search_works:
            issues.append("Document search failed")
        if not filter_works:
            issues.append("Document category filtering failed")
        if document_id and not delete_test:
            issues.append("Document deletion failed")
        
        print("❌ File Center integration has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "File Center integration has issues"

def test_conversation_integration():
    """Test that conversations with action triggers automatically generate documents"""
    print("\n" + "="*80)
    print("TESTING CONVERSATION INTEGRATION WITH DOCUMENT GENERATION")
    print("="*80)
    
    # This test requires a more complex setup with agents and conversation generation
    # We'll simulate a conversation with action triggers
    
    # 1. Create test agents
    agents = []
    for i in range(3):
        agent_data = {
            "name": f"Test Agent {i+1}",
            "archetype": "scientist",
            "goal": "Test conversation integration",
            "expertise": "Testing"
        }
        
        agent_test, agent_response = run_test(
            f"Create Test Agent {i+1}",
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
    
    # 2. Set up simulation state
    scenario_data = {
        "scenario": "Test Scenario for Document Generation"
    }
    
    scenario_test, _ = run_test(
        "Set Simulation Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=scenario_data
    )
    
    if not scenario_test:
        print("❌ Failed to set simulation scenario")
        return False, "Failed to set simulation scenario"
    
    # 3. Generate a conversation with action triggers
    # This is a bit tricky since we can't directly control the conversation content
    # We'll check if the conversation generation endpoint works and then check if documents were created
    
    conversation_test, conversation_response = run_test(
        "Generate Conversation",
        "/conversation/generate",
        method="POST",
        expected_keys=["messages", "round_number"]
    )
    
    if not conversation_test:
        print("❌ Failed to generate conversation")
        return False, "Failed to generate conversation"
    
    # 4. Check if any documents were created
    # Wait a moment for document generation to complete
    print("Waiting for potential document generation...")
    time.sleep(2)
    
    # Login first to get auth token if not already logged in
    if not auth_token:
        if not test_login():
            print("❌ Cannot check for documents without authentication")
            return False, "Authentication failed"
    
    documents_test, documents_response = run_test(
        "Check for Generated Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    # Note: We can't guarantee that a document was created since it depends on the conversation content
    # So we'll just check if the documents endpoint works
    
    # 5. Clean up - delete test agents
    for agent in agents:
        agent_id = agent.get("id")
        if agent_id:
            run_test(
                f"Delete Test Agent {agent_id}",
                f"/agents/{agent_id}",
                method="DELETE"
            )
    
    # Print summary
    print("\nCONVERSATION INTEGRATION SUMMARY:")
    
    if conversation_test and documents_test:
        print("✅ Conversation generation is working correctly!")
        print("✅ Documents endpoint is accessible after conversation generation")
        print("Note: We cannot guarantee that a document was created since it depends on the conversation content")
        return True, "Conversation integration endpoints are working correctly"
    else:
        issues = []
        if not conversation_test:
            issues.append("Conversation generation failed")
        if not documents_test:
            issues.append("Documents endpoint failed after conversation generation")
        
        print("❌ Conversation integration has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Conversation integration has issues"

def main():
    """Run tests for Action-Oriented Agent Behavior System and File Center"""
    print("Starting tests for Action-Oriented Agent Behavior System and File Center...")
    
    # Login first to get auth token for authenticated tests
    test_login()
    
    # 1. Test document categories endpoint
    categories_success, categories_message = test_document_categories()
    
    # 2. Test action trigger analysis
    action_trigger_success, action_trigger_message = test_action_trigger_analysis()
    
    # 3. Test document generation
    document_generation_success, document_generation_message = test_document_generation()
    
    # 4. Test File Center integration
    file_center_success, file_center_message = test_file_center_integration()
    
    # 5. Test conversation integration
    conversation_integration_success, conversation_integration_message = test_conversation_integration()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("ACTION-ORIENTED AGENT BEHAVIOR SYSTEM AND FILE CENTER ASSESSMENT")
    print("="*80)
    
    all_tests_passed = (
        categories_success and
        action_trigger_success and
        document_generation_success and
        file_center_success and
        conversation_integration_success
    )
    
    if all_tests_passed:
        print("✅ The Action-Oriented Agent Behavior System and File Center are working correctly!")
        print("✅ Document categories endpoint returns expected categories")
        print("✅ Action trigger analysis correctly detects document creation triggers")
        print("✅ Document generation creates properly formatted documents with metadata")
        print("✅ File Center allows creating, retrieving, searching, filtering, and deleting documents")
        print("✅ Conversation integration with document generation is functioning")
    else:
        print("❌ The Action-Oriented Agent Behavior System and File Center have issues:")
        if not categories_success:
            print(f"  - {categories_message}")
        if not action_trigger_success:
            print(f"  - {action_trigger_message}")
        if not document_generation_success:
            print(f"  - {document_generation_message}")
        if not file_center_success:
            print(f"  - {file_center_message}")
        if not conversation_integration_success:
            print(f"  - {conversation_integration_message}")
    print("="*80)

if __name__ == "__main__":
    main()
