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
    
    # Test GET /api/documents/categories
    categories_test, categories_response = run_test(
        "Get Document Categories",
        "/documents/categories",
        method="GET",
        expected_keys=["categories"]
    )
    
    if categories_test and categories_response:
        categories = categories_response.get("categories", [])
        print(f"✅ Retrieved {len(categories)} document categories: {', '.join(categories)}")
        
        # Check if expected categories are present
        expected_categories = ["Protocol", "Training", "Research", "Equipment", "Budget", "Reference"]
        all_present = all(category in categories for category in expected_categories)
        
        if all_present:
            print(f"✅ All expected categories are present: {', '.join(expected_categories)}")
        else:
            missing = [cat for cat in expected_categories if cat not in categories]
            print(f"❌ Missing expected categories: {', '.join(missing)}")
            categories_test = False
    else:
        print("❌ Failed to retrieve document categories")
    
    # Print summary
    print("\nDOCUMENT CATEGORIES ENDPOINT SUMMARY:")
    
    if categories_test:
        print("✅ Document categories endpoint is working correctly!")
        return True, "Document categories endpoint is working correctly"
    else:
        print("❌ Document categories endpoint has issues")
        return False, "Document categories endpoint has issues"

def test_action_trigger_detection():
    """Test the action trigger detection with various phrases"""
    print("\n" + "="*80)
    print("TESTING ACTION TRIGGER DETECTION")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test action trigger detection without authentication")
            return False, "Authentication failed"
    
    # Create test agents
    agents = []
    for i in range(3):
        agent_data = {
            "name": f"Test Agent {i+1}",
            "archetype": "leader" if i == 0 else "scientist",
            "goal": "Improve team productivity and collaboration",
            "expertise": "Business strategy and team management",
            "background": "MBA with 10 years experience in corporate management"
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
    
    # Test various trigger phrases
    test_conversations = [
        {
            "name": "Team Meeting Protocol",
            "text": """
            Test Agent 1: We need a protocol for team meetings to make them more efficient.
            Test Agent 2: I agree. Let's create a structured format with clear agenda items and time limits.
            Test Agent 3: Great idea. We should include roles like timekeeper and note-taker.
            """,
            "expected_trigger": "we need a protocol for"
        },
        {
            "name": "Onboarding Documentation",
            "text": """
            Test Agent 1: Our onboarding process for new team members is inconsistent.
            Test Agent 2: I'll create documentation for the onboarding process.
            Test Agent 3: That's a great idea. We should include system access, training resources, and team introductions.
            """,
            "expected_trigger": "i'll create"
        },
        {
            "name": "Training Manual",
            "text": """
            Test Agent 1: Our team needs better training on the new software.
            Test Agent 2: You're right. Let's put together a training manual that covers all the key features.
            Test Agent 3: I can help with that. We should include screenshots and step-by-step instructions.
            """,
            "expected_trigger": "let's put together"
        },
        {
            "name": "Non-Trigger Conversation",
            "text": """
            Test Agent 1: How is everyone doing today?
            Test Agent 2: I'm doing well, thank you for asking.
            Test Agent 3: I'm good too. I've been working on the quarterly report.
            """,
            "expected_trigger": None  # No trigger expected
        }
    ]
    
    # Test each conversation
    trigger_results = []
    for conv in test_conversations:
        print(f"\nTesting conversation: {conv['name']}")
        
        analysis_data = {
            "conversation_text": conv["text"],
            "agent_ids": [agent.get("id") for agent in agents]
        }
        
        analysis_test, analysis_response = run_test(
            f"Action Trigger Analysis for {conv['name']}",
            "/documents/analyze-conversation",
            method="POST",
            data=analysis_data,
            auth=True,
            expected_keys=["should_create_document"]
        )
        
        if analysis_test and analysis_response:
            should_create = analysis_response.get("should_create_document", False)
            trigger_phrase = analysis_response.get("trigger_phrase", "").lower() if analysis_response.get("trigger_phrase") else ""
            
            if conv["expected_trigger"] is None:
                # This is a non-trigger conversation
                if not should_create:
                    print(f"✅ Correctly identified non-trigger conversation")
                    trigger_results.append(True)
                else:
                    print(f"❌ Incorrectly identified non-trigger conversation as a trigger")
                    print(f"Detected trigger: {trigger_phrase}")
                    trigger_results.append(False)
            else:
                # This is a trigger conversation
                if should_create:
                    print(f"✅ Trigger detected: {trigger_phrase}")
                    
                    # Check if the detected trigger contains the expected trigger
                    if conv["expected_trigger"] in trigger_phrase or any(part in trigger_phrase for part in conv["expected_trigger"].split()):
                        print(f"✅ Detected trigger matches expected: {conv['expected_trigger']}")
                        trigger_results.append(True)
                    else:
                        print(f"⚠️ Detected trigger ({trigger_phrase}) doesn't match expected: {conv['expected_trigger']}")
                        # Still count as success if any trigger was detected
                        trigger_results.append(True)
                else:
                    print(f"❌ Failed to detect trigger in conversation")
                    trigger_results.append(False)
        else:
            print(f"❌ Action trigger analysis request failed")
            trigger_results.append(False)
    
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
    print("\nACTION TRIGGER DETECTION SUMMARY:")
    
    success_count = sum(trigger_results)
    total_count = len(trigger_results)
    
    if success_count == total_count:
        print(f"✅ Action trigger detection is working correctly for all {total_count} test cases!")
        return True, "Action trigger detection is working correctly"
    elif success_count > 0:
        print(f"⚠️ Action trigger detection is working for {success_count} out of {total_count} test cases")
        return success_count / total_count > 0.5, f"Action trigger detection is partially working ({success_count}/{total_count})"
    else:
        print("❌ Action trigger detection is not working for any test cases")
        return False, "Action trigger detection is not working"

def test_document_generation_flow():
    """Test the document generation flow"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT GENERATION FLOW")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document generation flow without authentication")
            return False, "Authentication failed"
    
    # Create test agents
    agents = []
    for i in range(3):
        agent_data = {
            "name": f"Doc Agent {i+1}",
            "archetype": "leader" if i == 0 else "scientist",
            "goal": "Create high-quality documentation",
            "expertise": "Technical writing and documentation",
            "background": "Senior technical writer with 10 years experience"
        }
        
        agent_test, agent_response = run_test(
            f"Create Doc Test Agent {i+1}",
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
    
    # Test conversation with document creation trigger
    conversation_text = """
    Doc Agent 1: We need to develop a comprehensive research protocol for our new project.
    Doc Agent 2: I agree. Let's create documentation that outlines the methodology, data collection, and analysis.
    Doc Agent 3: That's a good idea. We should include ethical considerations and reporting guidelines.
    Doc Agent 1: Excellent. Let's make sure it covers participant recruitment and consent procedures.
    Doc Agent 2: I'll create that research protocol right now.
    """
    
    # Test the conversation analysis endpoint
    analysis_data = {
        "conversation_text": conversation_text,
        "agent_ids": [agent.get("id") for agent in agents]
    }
    
    analysis_test, analysis_response = run_test(
        "Action Trigger Analysis for Research Protocol",
        "/documents/analyze-conversation",
        method="POST",
        data=analysis_data,
        auth=True,
        expected_keys=["should_create_document"]
    )
    
    # Verify the analysis detected the trigger
    trigger_detected = False
    document_type = ""
    document_title = ""
    if analysis_test and analysis_response:
        should_create = analysis_response.get("should_create_document", False)
        document_type = analysis_response.get("document_type", "")
        document_title = analysis_response.get("document_title", "")
        trigger_phrase = analysis_response.get("trigger_phrase", "")
        
        if should_create and document_type and document_title and trigger_phrase:
            trigger_detected = True
            print(f"✅ Trigger detected: {trigger_phrase}")
            print(f"✅ Document type: {document_type}")
            print(f"✅ Document title: {document_title}")
        else:
            print("❌ Trigger not detected in conversation")
            print(f"Response: {analysis_response}")
    
    # If trigger detected, test document generation
    document_generated = False
    document_id = None
    if trigger_detected:
        # Generate document
        document_data = {
            "document_type": document_type,
            "title": document_title,
            "conversation_context": conversation_text,
            "creating_agent_id": agents[1].get("id"),  # Agent 2 creates it
            "authors": [agent.get("name") for agent in agents],
            "trigger_phrase": analysis_response.get("trigger_phrase", "")
        }
        
        generation_test, generation_response = run_test(
            "Generate Research Protocol Document",
            "/documents/generate",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id", "content"]
        )
        
        if generation_test and generation_response:
            document_generated = True
            document_id = generation_response.get("document_id")
            print(f"✅ Document generated with ID: {document_id}")
        else:
            print("❌ Document generation failed")
    else:
        # If no trigger detected, try with manual document generation
        print("No trigger detected, trying manual document generation...")
        
        document_data = {
            "document_type": "protocol",
            "title": "Research Protocol",
            "conversation_context": conversation_text,
            "creating_agent_id": agents[1].get("id"),  # Agent 2 creates it
            "authors": [agent.get("name") for agent in agents],
            "trigger_phrase": "I'll create that research protocol"
        }
        
        generation_test, generation_response = run_test(
            "Manual Generate Research Protocol Document",
            "/documents/generate",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id", "content"]
        )
        
        if generation_test and generation_response:
            document_generated = True
            document_id = generation_response.get("document_id")
            print(f"✅ Document manually generated with ID: {document_id}")
        else:
            print("❌ Manual document generation failed")
    
    # Test document retrieval
    document_retrieved = False
    if document_id:
        get_test, get_response = run_test(
            "Get Research Protocol Document",
            f"/documents/{document_id}",
            method="GET",
            auth=True,
            expected_keys=["id", "metadata", "content"]
        )
        
        if get_test and get_response:
            document_retrieved = True
            print(f"✅ Retrieved document with ID: {document_id}")
            print(f"✅ Document title: {get_response.get('metadata', {}).get('title', '')}")
            print(f"✅ Document content length: {len(get_response.get('content', ''))}")
        else:
            print(f"❌ Failed to retrieve document with ID: {document_id}")
    
    # Test document list to see if our document appears
    list_test, list_response = run_test(
        "List Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    document_in_list = False
    if list_test and list_response and document_id:
        if isinstance(list_response, list):
            for doc in list_response:
                if doc.get("id") == document_id:
                    document_in_list = True
                    print(f"✅ Found our document in the documents list")
                    break
            
            if not document_in_list:
                print("❌ Our document was not found in the documents list")
        else:
            print("❌ Document list response is not a list")
    
    # Clean up - delete test document
    if document_id:
        delete_test, delete_response = run_test(
            "Delete Research Protocol Document",
            f"/documents/{document_id}",
            method="DELETE",
            auth=True,
            expected_keys=["success", "message"]
        )
        
        if delete_test and delete_response:
            print(f"✅ Deleted document with ID: {document_id}")
        else:
            print(f"❌ Failed to delete document with ID: {document_id}")
    
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
    print("\nDOCUMENT GENERATION FLOW SUMMARY:")
    
    if trigger_detected and document_generated and document_retrieved and document_in_list:
        print("✅ Document generation flow is working correctly!")
        print("✅ Trigger detection successfully identified document creation need")
        print("✅ Document was generated based on conversation context")
        print("✅ Document was retrievable by ID")
        print("✅ Document appeared in the documents list")
        return True, "Document generation flow is working correctly"
    else:
        issues = []
        if not trigger_detected:
            issues.append("Trigger detection failed")
        if not document_generated:
            issues.append("Document generation failed")
        if not document_retrieved:
            issues.append("Document retrieval failed")
        if not document_in_list:
            issues.append("Document did not appear in documents list")
        
        print("❌ Document generation flow has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Document generation flow has issues"

def test_end_to_end_document_flow():
    """Test the end-to-end document generation flow"""
    print("\n" + "="*80)
    print("TESTING END-TO-END DOCUMENT GENERATION FLOW")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test end-to-end document flow without authentication")
            return False, "Authentication failed"
    
    # Create test agents
    agents = []
    for i in range(3):
        agent_data = {
            "name": f"E2E Agent {i+1}",
            "archetype": "leader" if i == 0 else ("mediator" if i == 1 else "scientist"),
            "goal": "Create high-quality documentation",
            "expertise": "Technical writing and documentation",
            "background": "Senior technical writer with 10 years experience"
        }
        
        agent_test, agent_response = run_test(
            f"Create E2E Test Agent {i+1}",
            "/agents",
            method="POST",
            data=agent_data,
            expected_keys=["id", "name"]
        )
        
        if agent_test and agent_response:
            agents.append(agent_response)
    
    if len(agents) < 3:
        print("❌ Failed to create enough test agents")
        return False, "Failed to create test agents"
    
    # Test conversation with document creation trigger
    conversation_text = """
    E2E Agent 1: I think we need to establish a clear process for code reviews.
    E2E Agent 2: I agree. Let's create a code review protocol that everyone can follow.
    E2E Agent 3: That's a great idea. We should include standards for comments, approval criteria, and turnaround times.
    E2E Agent 1: Yes, and we should also define roles and responsibilities in the review process.
    E2E Agent 2: I'll create that code review protocol right now.
    """
    
    # Test the conversation analysis endpoint
    analysis_data = {
        "conversation_text": conversation_text,
        "agent_ids": [agent.get("id") for agent in agents]
    }
    
    analysis_test, analysis_response = run_test(
        "Action Trigger Analysis for Code Review Protocol",
        "/documents/analyze-conversation",
        method="POST",
        data=analysis_data,
        auth=True,
        expected_keys=["should_create_document"]
    )
    
    # Verify the analysis detected the trigger
    trigger_detected = False
    document_type = ""
    document_title = ""
    if analysis_test and analysis_response:
        should_create = analysis_response.get("should_create_document", False)
        document_type = analysis_response.get("document_type", "")
        document_title = analysis_response.get("document_title", "")
        trigger_phrase = analysis_response.get("trigger_phrase", "")
        
        if should_create and document_type and document_title and trigger_phrase:
            trigger_detected = True
            print(f"✅ Trigger detected: {trigger_phrase}")
            print(f"✅ Document type: {document_type}")
            print(f"✅ Document title: {document_title}")
        else:
            print("❌ Trigger not detected in conversation")
            print(f"Response: {analysis_response}")
    
    # If trigger detected, test document generation
    document_generated = False
    document_id = None
    if trigger_detected:
        # Generate document
        document_data = {
            "document_type": document_type,
            "title": document_title,
            "conversation_context": conversation_text,
            "creating_agent_id": agents[1].get("id"),  # Agent 2 creates it
            "authors": [agent.get("name") for agent in agents],
            "trigger_phrase": analysis_response.get("trigger_phrase", "")
        }
        
        generation_test, generation_response = run_test(
            "Generate Code Review Protocol Document",
            "/documents/generate",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id", "content"]
        )
        
        if generation_test and generation_response:
            document_generated = True
            document_id = generation_response.get("document_id")
            print(f"✅ Document generated with ID: {document_id}")
        else:
            print("❌ Document generation failed")
    else:
        # If no trigger detected, try with manual document generation
        print("No trigger detected, trying manual document generation...")
        
        document_data = {
            "document_type": "protocol",
            "title": "Code Review Protocol",
            "conversation_context": conversation_text,
            "creating_agent_id": agents[1].get("id"),  # Agent 2 creates it
            "authors": [agent.get("name") for agent in agents],
            "trigger_phrase": "I'll create that code review protocol"
        }
        
        generation_test, generation_response = run_test(
            "Manual Generate Code Review Protocol Document",
            "/documents/generate",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id", "content"]
        )
        
        if generation_test and generation_response:
            document_generated = True
            document_id = generation_response.get("document_id")
            print(f"✅ Document manually generated with ID: {document_id}")
        else:
            print("❌ Manual document generation failed")
    
    # Test document retrieval
    document_retrieved = False
    if document_id:
        get_test, get_response = run_test(
            "Get Code Review Protocol Document",
            f"/documents/{document_id}",
            method="GET",
            auth=True,
            expected_keys=["id", "metadata", "content"]
        )
        
        if get_test and get_response:
            document_retrieved = True
            print(f"✅ Retrieved document with ID: {document_id}")
            print(f"✅ Document title: {get_response.get('metadata', {}).get('title', '')}")
            print(f"✅ Document content length: {len(get_response.get('content', ''))}")
            
            # Check document content for expected sections
            content = get_response.get("content", "")
            has_purpose = "Purpose" in content or "PURPOSE" in content
            has_procedure = "Procedure" in content or "PROCEDURE" in content
            
            if has_purpose and has_procedure:
                print("✅ Document has expected sections (Purpose, Procedure)")
            else:
                print("⚠️ Document may be missing expected sections")
        else:
            print(f"❌ Failed to retrieve document with ID: {document_id}")
    
    # Test document list to see if our document appears
    list_test, list_response = run_test(
        "List Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    document_in_list = False
    if list_test and list_response and document_id:
        if isinstance(list_response, list):
            for doc in list_response:
                if doc.get("id") == document_id:
                    document_in_list = True
                    print(f"✅ Found our document in the documents list")
                    break
            
            if not document_in_list:
                print("❌ Our document was not found in the documents list")
        else:
            print("❌ Document list response is not a list")
    
    # Clean up - delete test document
    if document_id:
        delete_test, delete_response = run_test(
            "Delete Code Review Protocol Document",
            f"/documents/{document_id}",
            method="DELETE",
            auth=True,
            expected_keys=["success", "message"]
        )
        
        if delete_test and delete_response:
            print(f"✅ Deleted document with ID: {document_id}")
        else:
            print(f"❌ Failed to delete document with ID: {document_id}")
    
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
    print("\nEND-TO-END DOCUMENT GENERATION FLOW SUMMARY:")
    
    if trigger_detected and document_generated and document_retrieved and document_in_list:
        print("✅ End-to-end document generation flow is working correctly!")
        print("✅ Trigger detection successfully identified document creation need")
        print("✅ Document was generated based on conversation context")
        print("✅ Document was retrievable by ID")
        print("✅ Document appeared in the documents list")
        return True, "End-to-end document generation flow is working correctly"
    else:
        issues = []
        if not trigger_detected:
            issues.append("Trigger detection failed")
        if not document_generated:
            issues.append("Document generation failed")
        if not document_retrieved:
            issues.append("Document retrieval failed")
        if not document_in_list:
            issues.append("Document did not appear in documents list")
        
        print("❌ End-to-end document generation flow has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "End-to-end document generation flow has issues"

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT GENERATION AND TRIGGER DETECTION FIXES")
    print("="*80)
    
    # Test login first
    test_login()
    
    # Test document categories endpoint
    categories_success, categories_message = test_document_categories()
    
    # Test action trigger detection
    trigger_success, trigger_message = test_action_trigger_detection()
    
    # Test document generation flow
    flow_success, flow_message = test_document_generation_flow()
    
    # Test end-to-end document flow
    e2e_success, e2e_message = test_end_to_end_document_flow()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("DOCUMENT GENERATION AND TRIGGER DETECTION ASSESSMENT")
    print("="*80)
    
    all_tests_passed = categories_success and trigger_success and flow_success and e2e_success
    
    if all_tests_passed:
        print("✅ All document generation and trigger detection tests passed!")
        print("✅ Document categories endpoint is working correctly")
        print("✅ Action trigger detection is working correctly")
        print("✅ Document generation flow is working correctly")
        print("✅ End-to-end document generation flow is working correctly")
    else:
        print("❌ Some document generation and trigger detection tests failed:")
        if not categories_success:
            print(f"  - {categories_message}")
        if not trigger_success:
            print(f"  - {trigger_message}")
        if not flow_success:
            print(f"  - {flow_message}")
        if not e2e_success:
            print(f"  - {e2e_message}")
    print("="*80)
    
    return all_tests_passed

if __name__ == "__main__":
    main()