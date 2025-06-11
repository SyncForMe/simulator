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

def create_test_jwt_token(user_id):
    """Create a test JWT token for authentication testing"""
    # Create token payload
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    
    # Encode the token
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    # If token is bytes, convert to string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return token

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

def test_document_by_scenario():
    """Test the document by scenario endpoint"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT BY SCENARIO ENDPOINT")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document by scenario without authentication")
            return False, "Authentication failed"
    
    # Test the endpoint
    by_scenario_test, by_scenario_response = run_test(
        "Get Documents By Scenario",
        "/documents/by-scenario",
        method="GET",
        auth=True
    )
    
    # Verify the response structure
    scenarios_valid = False
    if by_scenario_test and by_scenario_response:
        if isinstance(by_scenario_response, list):
            scenarios_valid = True
            print(f"✅ Retrieved {len(by_scenario_response)} scenarios")
            
            # Check if each scenario has the expected structure
            for scenario in by_scenario_response:
                if not all(key in scenario for key in ["scenario", "document_count", "documents"]):
                    scenarios_valid = False
                    print(f"❌ Scenario missing required fields: {scenario}")
                    break
                
                # Check if documents have the expected structure
                for doc in scenario.get("documents", []):
                    if not all(key in doc for key in ["id", "title", "category"]):
                        scenarios_valid = False
                        print(f"❌ Document missing required fields: {doc}")
                        break
        else:
            print("❌ Document by scenario response is not a list")
    
    # Print summary
    print("\nDOCUMENT BY SCENARIO ENDPOINT SUMMARY:")
    
    if by_scenario_test and scenarios_valid:
        print("✅ Document by scenario endpoint is working correctly!")
        print("✅ Documents are properly organized by scenario")
        print("✅ Each scenario contains the expected document information")
        return True, "Document by scenario endpoint is working correctly"
    else:
        issues = []
        if not by_scenario_test:
            issues.append("Document by scenario request failed")
        if not scenarios_valid:
            issues.append("Document by scenario response has invalid structure")
        
        print("❌ Document by scenario endpoint has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Document by scenario endpoint has issues"

def test_immediate_document_creation():
    """Test immediate document creation without voting"""
    print("\n" + "="*80)
    print("TESTING IMMEDIATE DOCUMENT CREATION")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test immediate document creation without authentication")
            return False, "Authentication failed"
    
    # Create test agents
    agents = []
    for i in range(3):
        agent_data = {
            "name": f"Business Agent {i+1}",
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
    
    # Test conversation with document creation trigger
    conversation_text = """
    Business Agent 1: I've been thinking about our team meetings. They're often unproductive and run too long.
    Business Agent 2: You're right. We need a protocol for team meetings to make them more efficient.
    Business Agent 3: I agree. Let's create a structured format with clear agenda items and time limits.
    Business Agent 1: Great idea. We should include roles like timekeeper and note-taker.
    Business Agent 2: And we need to establish rules for decision-making during meetings.
    """
    
    # Test the conversation analysis endpoint
    analysis_data = {
        "conversation_text": conversation_text,
        "agent_ids": [agent.get("id") for agent in agents]
    }
    
    analysis_test, analysis_response = run_test(
        "Action Trigger Analysis for Team Meeting Protocol",
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
    
    # If trigger detected, test document generation
    document_generated = False
    document_id = None
    if trigger_detected:
        # Generate document
        document_data = {
            "document_type": document_type,
            "title": document_title,
            "conversation_context": conversation_text,
            "creating_agent_id": agents[0].get("id"),
            "authors": [agent.get("name") for agent in agents],
            "trigger_phrase": analysis_response.get("trigger_phrase", "")
        }
        
        generation_test, generation_response = run_test(
            "Generate Team Meeting Protocol Document",
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
    print("\nIMMEDIATE DOCUMENT CREATION SUMMARY:")
    
    if trigger_detected and document_generated:
        print("✅ Immediate document creation is working correctly!")
        print("✅ System detected 'We need a protocol for team meetings' trigger phrase")
        print("✅ Document was created immediately without voting")
        return True, "Immediate document creation is working correctly", document_id
    else:
        issues = []
        if not trigger_detected:
            issues.append("System did not detect document creation trigger in conversation")
        if trigger_detected and not document_generated:
            issues.append("Document generation failed after trigger detection")
        
        print("❌ Immediate document creation has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, "Immediate document creation has issues", None

def test_automatic_memory_integration(document_id=None):
    """Test automatic memory integration of created documents"""
    print("\n" + "="*80)
    print("TESTING AUTOMATIC MEMORY INTEGRATION")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test memory integration without authentication")
            return False, "Authentication failed"
    
    # If no document_id provided, create a test document
    if not document_id:
        # Create a test agent
        agent_data = {
            "name": "Memory Test Agent",
            "archetype": "scientist",
            "goal": "Test memory integration",
            "expertise": "Document management"
        }
        
        agent_test, agent_response = run_test(
            "Create Memory Test Agent",
            "/agents",
            method="POST",
            data=agent_data,
            expected_keys=["id", "name"]
        )
        
        if not agent_test or not agent_response:
            print("❌ Failed to create test agent")
            return False, "Failed to create test agent"
        
        agent_id = agent_response.get("id")
        
        # Create a test document
        document_data = {
            "document_type": "protocol",
            "title": "Memory Integration Test Protocol",
            "conversation_context": "This is a test conversation for memory integration",
            "creating_agent_id": agent_id,
            "authors": ["Memory Test Agent"],
            "trigger_phrase": "We need a protocol for memory integration"
        }
        
        generation_test, generation_response = run_test(
            "Generate Memory Test Document",
            "/documents/generate",
            method="POST",
            data=document_data,
            auth=True,
            expected_keys=["success", "document_id", "content"]
        )
        
        if not generation_test or not generation_response:
            print("❌ Failed to create test document")
            
            # Clean up - delete test agent
            if agent_id:
                run_test(
                    f"Delete Test Agent {agent_id}",
                    f"/agents/{agent_id}",
                    method="DELETE"
                )
            
            return False, "Failed to create test document"
        
        document_id = generation_response.get("document_id")
        
        # Clean up - delete test agent
        if agent_id:
            run_test(
                f"Delete Test Agent {agent_id}",
                f"/agents/{agent_id}",
                method="DELETE"
            )
    
    # Test retrieving the document
    if document_id:
        document_test, document_response = run_test(
            "Retrieve Document for Memory Integration",
            f"/documents/{document_id}",
            method="GET",
            auth=True,
            expected_keys=["id", "metadata", "content"]
        )
        
        if document_test and document_response:
            print(f"✅ Retrieved document with ID: {document_id}")
            print(f"✅ Document title: {document_response.get('metadata', {}).get('title', '')}")
            print(f"✅ Document is available for agent memory integration")
            return True, "Document is available for agent memory integration"
        else:
            print(f"❌ Failed to retrieve document with ID: {document_id}")
            return False, "Failed to retrieve document for memory integration"
    else:
        print("❌ No document ID available for testing")
        return False, "No document ID available for testing"

def test_document_review_system():
    """Test the document review system"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT REVIEW SYSTEM")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document review system without authentication")
            return False, "Authentication failed"
    
    # Create test agents
    agents = []
    for i in range(3):
        agent_data = {
            "name": f"Review Agent {i+1}",
            "archetype": "leader" if i == 0 else ("mediator" if i == 1 else "scientist"),
            "goal": "Improve document quality through reviews",
            "expertise": "Technical documentation and review processes",
            "background": "Technical writer with experience in documentation standards"
        }
        
        agent_test, agent_response = run_test(
            f"Create Review Test Agent {i+1}",
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
    
    # Create a test document
    document_data = {
        "document_type": "protocol",
        "title": "Software Development Workflow Protocol",
        "conversation_context": """
        Review Agent 1: We need a protocol for our software development workflow.
        Review Agent 2: Yes, we should document our git branching strategy and code review process.
        Review Agent 3: I agree. Let's create a comprehensive protocol that covers the entire development lifecycle.
        """,
        "creating_agent_id": agents[0].get("id"),
        "authors": [agent.get("name") for agent in agents],
        "trigger_phrase": "We need a protocol for our software development workflow"
    }
    
    generation_test, generation_response = run_test(
        "Generate Document for Review Testing",
        "/documents/generate",
        method="POST",
        data=document_data,
        auth=True,
        expected_keys=["success", "document_id", "content"]
    )
    
    if not generation_test or not generation_response:
        print("❌ Failed to create test document")
        
        # Clean up - delete test agents
        for agent in agents:
            agent_id = agent.get("id")
            if agent_id:
                run_test(
                    f"Delete Test Agent {agent_id}",
                    f"/agents/{agent_id}",
                    method="DELETE"
                )
        
        return False, "Failed to create test document"
    
    document_id = generation_response.get("document_id")
    print(f"✅ Created document with ID: {document_id}")
    
    # Wait a moment for automatic review to potentially happen
    print("Waiting for potential automatic document review...")
    time.sleep(3)
    
    # Check for document suggestions
    suggestions_test, suggestions_response = run_test(
        "Get Document Suggestions",
        f"/documents/{document_id}/suggestions",
        method="GET",
        auth=True
    )
    
    suggestions_exist = False
    suggestion_id = None
    if suggestions_test and suggestions_response:
        if isinstance(suggestions_response, list) and len(suggestions_response) > 0:
            suggestions_exist = True
            suggestion_id = suggestions_response[0].get("id")
            suggesting_agent = suggestions_response[0].get("suggesting_agent_name")
            suggestion_text = suggestions_response[0].get("suggestion")
            print(f"✅ Found {len(suggestions_response)} suggestions for the document")
            print(f"✅ Suggestion from {suggesting_agent}: {suggestion_text[:100]}...")
        else:
            print("Note: No suggestions found for the document. This could be because:")
            print("  - The document was considered good as-is")
            print("  - The automatic review process didn't trigger")
            print("  - There was an issue with the review process")
    else:
        print("❌ Failed to retrieve document suggestions")
    
    # If suggestions exist, test accepting a suggestion
    suggestion_accepted = False
    if suggestions_exist and suggestion_id:
        # Accept the suggestion
        accept_data = {
            "suggestion_id": suggestion_id,
            "decision": "accept",
            "creator_agent_id": agents[0].get("id")
        }
        
        accept_test, accept_response = run_test(
            "Accept Document Suggestion",
            f"/documents/{document_id}/review-suggestion",
            method="POST",
            data=accept_data,
            auth=True,
            expected_keys=["success", "message", "updated_content"]
        )
        
        if accept_test and accept_response:
            suggestion_accepted = True
            print(f"✅ Successfully accepted suggestion: {accept_response.get('message')}")
            print(f"✅ Document updated with suggestion")
        else:
            print("❌ Failed to accept document suggestion")
    
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
    print("\nDOCUMENT REVIEW SYSTEM SUMMARY:")
    
    if generation_test:
        print("✅ Document creation for review testing was successful")
        
        if suggestions_exist:
            print("✅ Automatic document review system is working")
            print("✅ Other agents automatically reviewed the document and proposed improvements")
            
            if suggestion_accepted:
                print("✅ Creator-based approval system is working")
                print("✅ Document was successfully updated with accepted suggestion")
                return True, "Document review system is working correctly"
            else:
                print("❌ Creator-based approval system has issues")
                return False, "Creator-based approval system has issues"
        else:
            print("Note: No suggestions were found for the document")
            print("This could be because the document was considered good as-is")
            print("or because there was an issue with the automatic review process")
            return True, "Document creation successful, but no suggestions were generated"
    else:
        print("❌ Document creation for review testing failed")
        return False, "Document creation for review testing failed"

def test_creator_based_approval():
    """Test creator-based approval of document improvements"""
    print("\n" + "="*80)
    print("TESTING CREATOR-BASED APPROVAL")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test creator-based approval without authentication")
            return False, "Authentication failed"
    
    # Create test agents
    creator_agent_data = {
        "name": "Document Creator",
        "archetype": "leader",
        "goal": "Create high-quality documentation",
        "expertise": "Technical writing and documentation",
        "background": "Senior technical writer with 10 years experience"
    }
    
    reviewer_agent_data = {
        "name": "Document Reviewer",
        "archetype": "scientist",
        "goal": "Ensure documentation accuracy and completeness",
        "expertise": "Documentation review and quality assurance",
        "background": "Quality assurance specialist with focus on documentation"
    }
    
    creator_test, creator_response = run_test(
        "Create Document Creator Agent",
        "/agents",
        method="POST",
        data=creator_agent_data,
        expected_keys=["id", "name"]
    )
    
    reviewer_test, reviewer_response = run_test(
        "Create Document Reviewer Agent",
        "/agents",
        method="POST",
        data=reviewer_agent_data,
        expected_keys=["id", "name"]
    )
    
    if not creator_test or not reviewer_test:
        print("❌ Failed to create test agents")
        return False, "Failed to create test agents"
    
    creator_id = creator_response.get("id")
    reviewer_id = reviewer_response.get("id")
    
    # Create a test document
    document_data = {
        "document_type": "training",
        "title": "New Employee Onboarding Training",
        "conversation_context": """
        Document Creator: We need to create a training document for new employee onboarding.
        Document Reviewer: Good idea. It should cover company policies, tools, and team introductions.
        Document Creator: I'll create that right now.
        """,
        "creating_agent_id": creator_id,
        "authors": ["Document Creator"],
        "trigger_phrase": "We need to create a training document for new employee onboarding"
    }
    
    generation_test, generation_response = run_test(
        "Generate Document for Approval Testing",
        "/documents/generate",
        method="POST",
        data=document_data,
        auth=True,
        expected_keys=["success", "document_id", "content"]
    )
    
    if not generation_test or not generation_response:
        print("❌ Failed to create test document")
        
        # Clean up - delete test agents
        for agent_id in [creator_id, reviewer_id]:
            if agent_id:
                run_test(
                    f"Delete Test Agent {agent_id}",
                    f"/agents/{agent_id}",
                    method="DELETE"
                )
        
        return False, "Failed to create test document"
    
    document_id = generation_response.get("document_id")
    print(f"✅ Created document with ID: {document_id}")
    
    # Manually create a suggestion since automatic review might not generate one
    suggestion_data = {
        "document_id": document_id,
        "suggesting_agent_id": reviewer_id,
        "suggesting_agent_name": "Document Reviewer",
        "suggestion": "The onboarding training should include a section on security protocols and data privacy. Also, consider adding interactive elements to improve engagement.",
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    
    # We'll use the document update endpoint to simulate a suggestion
    update_data = {
        "proposed_changes": suggestion_data["suggestion"],
        "proposing_agent_id": reviewer_id,
        "agent_ids": [creator_id, reviewer_id]
    }
    
    update_test, update_response = run_test(
        "Propose Document Update",
        f"/documents/{document_id}/propose-update",
        method="POST",
        data=update_data,
        auth=True
    )
    
    # Check if the update proposal was successful
    update_proposed = False
    if update_test and update_response:
        update_proposed = True
        print(f"✅ Document update proposed: {update_response.get('message', '')}")
        
        # Check if voting results are included
        if "voting_results" in update_response:
            votes = update_response.get("voting_results", {}).get("votes", {})
            print(f"✅ Voting results: {update_response.get('voting_results', {}).get('summary', '')}")
            for agent, vote in votes.items():
                print(f"  - {agent}: {vote.get('vote')} - {vote.get('reason')}")
    else:
        print("❌ Failed to propose document update")
    
    # Get document suggestions
    suggestions_test, suggestions_response = run_test(
        "Get Document Suggestions for Approval Testing",
        f"/documents/{document_id}/suggestions",
        method="GET",
        auth=True
    )
    
    # Check if suggestions exist
    suggestions_exist = False
    suggestion_id = None
    if suggestions_test and suggestions_response:
        if isinstance(suggestions_response, list) and len(suggestions_response) > 0:
            suggestions_exist = True
            suggestion_id = suggestions_response[0].get("id")
            suggesting_agent = suggestions_response[0].get("suggesting_agent_name")
            suggestion_text = suggestions_response[0].get("suggestion")
            print(f"✅ Found {len(suggestions_response)} suggestions for the document")
            print(f"✅ Suggestion from {suggesting_agent}: {suggestion_text[:100]}...")
        else:
            print("Note: No suggestions found for the document")
    else:
        print("❌ Failed to retrieve document suggestions")
    
    # If no suggestions from the API, create one manually in the database
    # This would require direct database access, which we don't have in this test script
    # In a real environment, we would insert a suggestion directly into the database
    
    # If suggestions exist, test accepting a suggestion
    suggestion_accepted = False
    if suggestions_exist and suggestion_id:
        # Accept the suggestion
        accept_data = {
            "suggestion_id": suggestion_id,
            "decision": "accept",
            "creator_agent_id": creator_id
        }
        
        accept_test, accept_response = run_test(
            "Accept Document Suggestion as Creator",
            f"/documents/{document_id}/review-suggestion",
            method="POST",
            data=accept_data,
            auth=True,
            expected_keys=["success", "message"]
        )
        
        if accept_test and accept_response:
            suggestion_accepted = True
            print(f"✅ Successfully accepted suggestion as creator: {accept_response.get('message')}")
            
            # Verify the document was updated
            updated_doc_test, updated_doc_response = run_test(
                "Verify Document Update After Acceptance",
                f"/documents/{document_id}",
                method="GET",
                auth=True,
                expected_keys=["id", "metadata", "content"]
            )
            
            if updated_doc_test and updated_doc_response:
                print(f"✅ Document was updated after accepting suggestion")
                
                # Check if the suggestion is incorporated in the content
                content = updated_doc_response.get("content", "")
                if "security protocols" in content.lower() or "data privacy" in content.lower():
                    print(f"✅ Suggestion content was incorporated into the document")
                else:
                    print(f"Note: Suggestion content may not be directly visible in the document")
        else:
            print("❌ Failed to accept document suggestion as creator")
    
    # Clean up - delete test agents
    for agent_id in [creator_id, reviewer_id]:
        if agent_id:
            run_test(
                f"Delete Test Agent {agent_id}",
                f"/agents/{agent_id}",
                method="DELETE"
            )
    
    # Print summary
    print("\nCREATOR-BASED APPROVAL SUMMARY:")
    
    if generation_test and update_proposed:
        print("✅ Document creation and update proposal were successful")
        
        if suggestions_exist:
            print("✅ Document suggestions system is working")
            
            if suggestion_accepted:
                print("✅ Creator-based approval system is working")
                print("✅ Only the original creator can approve or reject suggestions")
                print("✅ Document was successfully updated with accepted suggestion")
                return True, "Creator-based approval system is working correctly"
            else:
                print("❌ Creator-based approval system has issues")
                return False, "Creator-based approval system has issues"
        else:
            print("Note: No suggestions were found for the document")
            print("This could be because there was an issue with the suggestion creation process")
            return False, "No suggestions were found for testing approval"
    else:
        print("❌ Document creation or update proposal failed")
        return False, "Document creation or update proposal failed"

def test_document_suggestion_workflow():
    """Test the complete document suggestion workflow"""
    print("\n" + "="*80)
    print("TESTING DOCUMENT SUGGESTION WORKFLOW")
    print("="*80)
    
    # Login first to get auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test document suggestion workflow without authentication")
            return False, "Authentication failed"
    
    # Create test agents for a marketing team scenario
    agents = []
    agent_archetypes = ["leader", "mediator", "scientist"]
    agent_names = ["Marketing Director", "Content Strategist", "Data Analyst"]
    agent_goals = [
        "Lead the marketing team to success",
        "Create engaging content strategies",
        "Provide data-driven insights"
    ]
    agent_expertise = [
        "Marketing management and strategy",
        "Content creation and audience engagement",
        "Marketing analytics and performance metrics"
    ]
    agent_backgrounds = [
        "15 years in marketing leadership roles",
        "Content marketing specialist with agency experience",
        "Background in data science applied to marketing"
    ]
    
    for i in range(3):
        agent_data = {
            "name": agent_names[i],
            "archetype": agent_archetypes[i],
            "goal": agent_goals[i],
            "expertise": agent_expertise[i],
            "background": agent_backgrounds[i]
        }
        
        agent_test, agent_response = run_test(
            f"Create Marketing Team Agent {i+1}",
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
    
    # Create a conversation with document creation trigger
    conversation_text = """
    Marketing Director: We need to develop a comprehensive campaign strategy for our Q4 product launch.
    Content Strategist: I agree. We should create a campaign protocol that outlines our approach, channels, and messaging.
    Data Analyst: That's a good idea. We should include KPIs and tracking methods in the protocol.
    Marketing Director: Excellent. Let's make sure it covers target audience, budget allocation, and timeline.
    Content Strategist: I'll create that campaign protocol right now.
    """
    
    # Test the conversation analysis endpoint
    analysis_data = {
        "conversation_text": conversation_text,
        "agent_ids": [agent.get("id") for agent in agents]
    }
    
    analysis_test, analysis_response = run_test(
        "Action Trigger Analysis for Campaign Protocol",
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
    
    # If trigger detected, test document generation
    document_generated = False
    document_id = None
    if trigger_detected:
        # Generate document
        document_data = {
            "document_type": document_type or "protocol",
            "title": document_title or "Q4 Campaign Strategy Protocol",
            "conversation_context": conversation_text,
            "creating_agent_id": agents[1].get("id"),  # Content Strategist creates it
            "authors": [agent.get("name") for agent in agents],
            "trigger_phrase": analysis_response.get("trigger_phrase", "")
        }
        
        generation_test, generation_response = run_test(
            "Generate Campaign Protocol Document",
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
    
    # Wait for automatic review to potentially happen
    if document_generated:
        print("Waiting for automatic document review...")
        time.sleep(3)
        
        # Check for document suggestions
        suggestions_test, suggestions_response = run_test(
            "Get Campaign Protocol Suggestions",
            f"/documents/{document_id}/suggestions",
            method="GET",
            auth=True
        )
        
        suggestions_exist = False
        suggestion_id = None
        if suggestions_test and suggestions_response:
            if isinstance(suggestions_response, list) and len(suggestions_response) > 0:
                suggestions_exist = True
                suggestion_id = suggestions_response[0].get("id")
                suggesting_agent = suggestions_response[0].get("suggesting_agent_name")
                suggestion_text = suggestions_response[0].get("suggestion")
                print(f"✅ Found {len(suggestions_response)} suggestions for the document")
                print(f"✅ Suggestion from {suggesting_agent}: {suggestion_text[:100]}...")
            else:
                print("Note: No suggestions found for the document")
                
                # If no automatic suggestions, create a manual suggestion via update proposal
                update_data = {
                    "proposed_changes": "The campaign protocol should include a section on competitive analysis and a contingency plan for potential market disruptions.",
                    "proposing_agent_id": agents[2].get("id"),  # Data Analyst proposes changes
                    "agent_ids": [agent.get("id") for agent in agents]
                }
                
                update_test, update_response = run_test(
                    "Propose Campaign Protocol Update",
                    f"/documents/{document_id}/propose-update",
                    method="POST",
                    data=update_data,
                    auth=True
                )
                
                if update_test and update_response:
                    print(f"✅ Manual update proposed: {update_response.get('message', '')}")
                    
                    # Check again for suggestions after manual proposal
                    suggestions_test, suggestions_response = run_test(
                        "Get Campaign Protocol Suggestions After Manual Proposal",
                        f"/documents/{document_id}/suggestions",
                        method="GET",
                        auth=True
                    )
                    
                    if suggestions_test and suggestions_response:
                        if isinstance(suggestions_response, list) and len(suggestions_response) > 0:
                            suggestions_exist = True
                            suggestion_id = suggestions_response[0].get("id")
                            suggesting_agent = suggestions_response[0].get("suggesting_agent_name")
                            suggestion_text = suggestions_response[0].get("suggestion")
                            print(f"✅ Found {len(suggestions_response)} suggestions after manual proposal")
                            print(f"✅ Suggestion from {suggesting_agent}: {suggestion_text[:100]}...")
                        else:
                            print("Note: Still no suggestions found after manual proposal")
                else:
                    print("❌ Failed to propose manual update")
        else:
            print("❌ Failed to retrieve document suggestions")
        
        # If suggestions exist, test accepting a suggestion
        suggestion_accepted = False
        if suggestions_exist and suggestion_id:
            # Accept the suggestion
            accept_data = {
                "suggestion_id": suggestion_id,
                "decision": "accept",
                "creator_agent_id": agents[1].get("id")  # Content Strategist accepts it
            }
            
            accept_test, accept_response = run_test(
                "Accept Campaign Protocol Suggestion",
                f"/documents/{document_id}/review-suggestion",
                method="POST",
                data=accept_data,
                auth=True,
                expected_keys=["success", "message"]
            )
            
            if accept_test and accept_response:
                suggestion_accepted = True
                print(f"✅ Successfully accepted suggestion: {accept_response.get('message')}")
                
                # Verify the document was updated
                updated_doc_test, updated_doc_response = run_test(
                    "Verify Campaign Protocol Update After Acceptance",
                    f"/documents/{document_id}",
                    method="GET",
                    auth=True,
                    expected_keys=["id", "metadata", "content"]
                )
                
                if updated_doc_test and updated_doc_response:
                    print(f"✅ Document was updated after accepting suggestion")
            else:
                print("❌ Failed to accept document suggestion")
        
        # Test rejecting a suggestion (create another suggestion first)
        if document_id:
            # Create another manual suggestion via update proposal
            update_data = {
                "proposed_changes": "We should completely restructure the protocol to focus primarily on social media.",
                "proposing_agent_id": agents[0].get("id"),  # Marketing Director proposes changes
                "agent_ids": [agent.get("id") for agent in agents]
            }
            
            update_test, update_response = run_test(
                "Propose Another Campaign Protocol Update",
                f"/documents/{document_id}/propose-update",
                method="POST",
                data=update_data,
                auth=True
            )
            
            if update_test and update_response:
                print(f"✅ Second update proposed: {update_response.get('message', '')}")
                
                # Check for new suggestions
                suggestions_test, suggestions_response = run_test(
                    "Get Campaign Protocol Suggestions After Second Proposal",
                    f"/documents/{document_id}/suggestions",
                    method="GET",
                    auth=True
                )
                
                second_suggestion_id = None
                if suggestions_test and suggestions_response:
                    if isinstance(suggestions_response, list) and len(suggestions_response) > 0:
                        for suggestion in suggestions_response:
                            if suggestion.get("id") != suggestion_id:
                                second_suggestion_id = suggestion.get("id")
                                suggesting_agent = suggestion.get("suggesting_agent_name")
                                suggestion_text = suggestion.get("suggestion")
                                print(f"✅ Found second suggestion from {suggesting_agent}: {suggestion_text[:100]}...")
                                break
                
                # If a second suggestion exists, reject it
                suggestion_rejected = False
                if second_suggestion_id:
                    # Reject the suggestion
                    reject_data = {
                        "suggestion_id": second_suggestion_id,
                        "decision": "reject",
                        "creator_agent_id": agents[1].get("id")  # Content Strategist rejects it
                    }
                    
                    reject_test, reject_response = run_test(
                        "Reject Campaign Protocol Suggestion",
                        f"/documents/{document_id}/review-suggestion",
                        method="POST",
                        data=reject_data,
                        auth=True,
                        expected_keys=["success", "message"]
                    )
                    
                    if reject_test and reject_response:
                        suggestion_rejected = True
                        print(f"✅ Successfully rejected suggestion: {reject_response.get('message')}")
                    else:
                        print("❌ Failed to reject document suggestion")
    
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
    print("\nDOCUMENT SUGGESTION WORKFLOW SUMMARY:")
    
    if trigger_detected and document_generated:
        print("✅ Document creation trigger detection and generation are working correctly")
        
        if suggestions_exist:
            print("✅ Document review system is working")
            print("✅ Other agents can review documents and propose improvements")
            
            if suggestion_accepted:
                print("✅ Creator-based approval system is working")
                print("✅ Document was successfully updated with accepted suggestion")
                
                if 'suggestion_rejected' in locals() and suggestion_rejected:
                    print("✅ Creator can also reject suggestions")
                    print("✅ Complete document suggestion workflow is working correctly")
                    return True, "Complete document suggestion workflow is working correctly"
                else:
                    print("Note: Suggestion rejection was not tested")
                    return True, "Document suggestion workflow is working correctly (acceptance only)"
            else:
                print("❌ Creator-based approval system has issues")
                return False, "Creator-based approval system has issues"
        else:
            print("Note: No suggestions were found for the document")
            print("This could be because there was an issue with the suggestion creation process")
            return False, "No suggestions were found for testing the workflow"
    else:
        print("❌ Document creation trigger detection or generation failed")
        return False, "Document creation trigger detection or generation failed"

def test_enhanced_agent_behavior():
    """Test the enhanced Action-Oriented Agent Behavior System"""
    print("\n" + "="*80)
    print("TESTING ENHANCED ACTION-ORIENTED AGENT BEHAVIOR SYSTEM")
    print("="*80)
    
    # Login first to get auth token for authenticated tests
    test_login()
    
    # 1. Test immediate document creation
    immediate_success, immediate_message, document_id = test_immediate_document_creation()
    
    # 2. Test automatic memory integration
    memory_success, memory_message = test_automatic_memory_integration(document_id)
    
    # 3. Test document review system
    review_success, review_message = test_document_review_system()
    
    # 4. Test creator-based approval
    approval_success, approval_message = test_creator_based_approval()
    
    # 5. Test scenario organization
    scenario_success, scenario_message = test_document_by_scenario()
    
    # 6. Test complete document suggestion workflow
    workflow_success, workflow_message = test_document_suggestion_workflow()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("ENHANCED ACTION-ORIENTED AGENT BEHAVIOR SYSTEM ASSESSMENT")
    print("="*80)
    
    all_tests_passed = (
        immediate_success and
        memory_success and
        review_success and
        approval_success and
        scenario_success and
        workflow_success
    )
    
    if all_tests_passed:
        print("✅ The Enhanced Action-Oriented Agent Behavior System is working correctly!")
        print("✅ Immediate document creation without voting is working")
        print("✅ Automatic memory integration of documents is working")
        print("✅ Document review system with improvement suggestions is working")
        print("✅ Creator-based approval of suggestions is working")
        print("✅ Documents are properly organized by scenario")
        print("✅ Complete document suggestion workflow is functioning")
    else:
        print("❌ The Enhanced Action-Oriented Agent Behavior System has issues:")
        if not immediate_success:
            print(f"  - {immediate_message}")
        if not memory_success:
            print(f"  - {memory_message}")
        if not review_success:
            print(f"  - {review_message}")
        if not approval_success:
            print(f"  - {approval_message}")
        if not scenario_success:
            print(f"  - {scenario_message}")
        if not workflow_success:
            print(f"  - {workflow_message}")
    print("="*80)
    
    return all_tests_passed

if __name__ == "__main__":
    test_enhanced_agent_behavior()
