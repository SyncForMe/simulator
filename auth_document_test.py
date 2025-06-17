#!/usr/bin/env python3
"""
Test module for authentication system and enhanced document generation features
"""

import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid
import jwt
from datetime import datetime, timedelta
import re
import base64

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

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth=False, headers=None, params=None, measure_time=False):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth and auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        start_time = time.time()
        
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
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {json.dumps(dict(response.headers), indent=2)}")
        if measure_time:
            print(f"Response Time: {response_time:.4f} seconds")
        
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
        
        test_result = {
            "name": test_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": response.status_code,
            "expected_status": expected_status,
            "result": result
        }
        
        if measure_time:
            test_result["response_time"] = response_time
            
        test_results["tests"].append(test_result)
        
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

def test_email_password_login():
    """Test the email/password login endpoint"""
    global auth_token, test_user_id
    
    print("\n" + "="*80)
    print("TESTING EMAIL/PASSWORD LOGIN")
    print("="*80)
    
    # Test 1: Login with valid credentials
    print("\nTest 1: Login with valid credentials")
    
    login_data = {
        "email": "dino@cytonic.com",
        "password": "Observerinho8"
    }
    
    login_test, login_response = run_test(
        "Login with valid credentials",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if login_test and login_response:
        print("✅ Login successful")
        auth_token = login_response.get("access_token")
        user_data = login_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"User ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        
        # Verify token structure
        try:
            decoded_token = jwt.decode(auth_token, JWT_SECRET, algorithms=["HS256"])
            print(f"✅ JWT token is valid and contains: {decoded_token}")
            if "user_id" in decoded_token and "sub" in decoded_token:
                print("✅ JWT token contains required fields (user_id, sub)")
            else:
                print("❌ JWT token is missing required fields")
        except Exception as e:
            print(f"❌ JWT token validation failed: {e}")
    else:
        print("❌ Login failed")
    
    # Test 2: Login with wrong password
    print("\nTest 2: Login with wrong password")
    
    wrong_password_data = {
        "email": "dino@cytonic.com",
        "password": "WrongPassword123"
    }
    
    wrong_password_test, wrong_password_response = run_test(
        "Login with wrong password",
        "/auth/login",
        method="POST",
        data=wrong_password_data,
        expected_status=401
    )
    
    if wrong_password_test:
        print("✅ Login with wrong password correctly rejected")
    else:
        print("❌ Login with wrong password not properly handled")
    
    # Test 3: Login with non-existent email
    print("\nTest 3: Login with non-existent email")
    
    wrong_email_data = {
        "email": f"nonexistent.{uuid.uuid4()}@example.com",
        "password": "Observerinho8"
    }
    
    wrong_email_test, wrong_email_response = run_test(
        "Login with non-existent email",
        "/auth/login",
        method="POST",
        data=wrong_email_data,
        expected_status=401
    )
    
    if wrong_email_test:
        print("✅ Login with non-existent email correctly rejected")
    else:
        print("❌ Login with non-existent email not properly handled")
    
    # Test 4: Test protected endpoint with token
    print("\nTest 4: Test protected endpoint with token")
    
    # Use the token from login to access a protected endpoint
    if auth_token:
        protected_test, protected_response = run_test(
            "Access protected endpoint",
            "/documents",
            method="GET",
            auth=True
        )
        
        if protected_test:
            print("✅ Successfully accessed protected endpoint with token")
        else:
            print("❌ Failed to access protected endpoint with token")
    else:
        print("❌ Cannot test protected endpoint without valid token")
    
    # Print summary
    print("\nEMAIL/PASSWORD LOGIN SUMMARY:")
    
    # Check if all critical tests passed
    login_works = login_test
    token_works = protected_test if auth_token else False
    
    if login_works and token_works:
        print("✅ Email/password login is working correctly!")
        print("✅ Login endpoint is functioning properly")
        print("✅ JWT tokens are generated correctly")
        print("✅ Protected endpoints can be accessed with valid token")
        return True, "Email/password login is working correctly"
    else:
        issues = []
        if not login_works:
            issues.append("Login endpoint is not functioning properly")
        if not token_works:
            issues.append("JWT token authentication is not working properly")
        
        print("❌ Email/password login has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_guest_login():
    """Test the test-login (Continue as Guest) endpoint"""
    global auth_token, test_user_id
    
    print("\n" + "="*80)
    print("TESTING GUEST LOGIN")
    print("="*80)
    
    # Test 1: Test login endpoint
    print("\nTest 1: Test login endpoint")
    
    test_login_test, test_login_response = run_test(
        "Test Login Endpoint",
        "/auth/test-login",
        method="POST",
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if test_login_test and test_login_response:
        print("✅ Test login successful")
        auth_token = test_login_response.get("access_token")
        user_data = test_login_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"User ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        
        # Verify token structure
        try:
            decoded_token = jwt.decode(auth_token, JWT_SECRET, algorithms=["HS256"])
            print(f"✅ JWT token is valid and contains: {decoded_token}")
            if "user_id" in decoded_token and "sub" in decoded_token:
                print("✅ JWT token contains required fields (user_id, sub)")
            else:
                print("❌ JWT token is missing required fields")
        except Exception as e:
            print(f"❌ JWT token validation failed: {e}")
    else:
        print("❌ Test login failed")
    
    # Test 2: Test protected endpoint with token
    print("\nTest 2: Test protected endpoint with token")
    
    # Use the token from test login to access a protected endpoint
    if auth_token:
        protected_test, protected_response = run_test(
            "Access protected endpoint",
            "/documents",
            method="GET",
            auth=True
        )
        
        if protected_test:
            print("✅ Successfully accessed protected endpoint with token")
        else:
            print("❌ Failed to access protected endpoint with token")
    else:
        print("❌ Cannot test protected endpoint without valid token")
    
    # Print summary
    print("\nGUEST LOGIN SUMMARY:")
    
    # Check if all critical tests passed
    login_works = test_login_test
    token_works = protected_test if auth_token else False
    
    if login_works and token_works:
        print("✅ Guest login is working correctly!")
        print("✅ Test login endpoint is functioning properly")
        print("✅ JWT tokens are generated correctly")
        print("✅ Protected endpoints can be accessed with valid token")
        return True, "Guest login is working correctly"
    else:
        issues = []
        if not login_works:
            issues.append("Test login endpoint is not functioning properly")
        if not token_works:
            issues.append("JWT token authentication is not working properly")
        
        print("❌ Guest login has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_jwt_validation():
    """Test JWT token validation"""
    global auth_token, test_user_id
    
    print("\n" + "="*80)
    print("TESTING JWT TOKEN VALIDATION")
    print("="*80)
    
    # Ensure we have a valid token
    if not auth_token:
        print("❌ Cannot test JWT validation without a valid token")
        return False, "No valid token available"
    
    # Test 1: Access user profile with token
    print("\nTest 1: Access user profile with token")
    
    profile_test, profile_response = run_test(
        "Get User Profile",
        "/auth/me",
        method="GET",
        auth=True,
        expected_keys=["id", "email", "name"]
    )
    
    if profile_test and profile_response:
        print("✅ Successfully accessed user profile with token")
        if profile_response.get("id") == test_user_id:
            print("✅ User ID in profile matches token user ID")
        else:
            print("❌ User ID in profile does not match token user ID")
    else:
        print("❌ Failed to access user profile with token")
    
    # Test 2: Access protected endpoint with invalid token
    print("\nTest 2: Access protected endpoint with invalid token")
    
    # Create an invalid token
    invalid_token = auth_token[:-5] + "12345"
    
    invalid_token_test, invalid_token_response = run_test(
        "Access with Invalid Token",
        "/documents",
        method="GET",
        headers={"Authorization": f"Bearer {invalid_token}"},
        expected_status=401
    )
    
    if invalid_token_test:
        print("✅ Invalid token correctly rejected")
    else:
        print("❌ Invalid token not properly rejected")
    
    # Test 3: Access protected endpoint with expired token
    print("\nTest 3: Access protected endpoint with expired token")
    
    # Create an expired token
    payload = {
        "user_id": test_user_id,
        "sub": "test@example.com",
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    }
    expired_token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    expired_token_test, expired_token_response = run_test(
        "Access with Expired Token",
        "/documents",
        method="GET",
        headers={"Authorization": f"Bearer {expired_token}"},
        expected_status=401
    )
    
    if expired_token_test:
        print("✅ Expired token correctly rejected")
    else:
        print("❌ Expired token not properly rejected")
    
    # Print summary
    print("\nJWT TOKEN VALIDATION SUMMARY:")
    
    # Check if all critical tests passed
    profile_works = profile_test
    invalid_token_rejected = invalid_token_test
    expired_token_rejected = expired_token_test
    
    if profile_works and invalid_token_rejected and expired_token_rejected:
        print("✅ JWT token validation is working correctly!")
        print("✅ Valid tokens are accepted")
        print("✅ Invalid tokens are rejected")
        print("✅ Expired tokens are rejected")
        return True, "JWT token validation is working correctly"
    else:
        issues = []
        if not profile_works:
            issues.append("Valid tokens are not properly accepted")
        if not invalid_token_rejected:
            issues.append("Invalid tokens are not properly rejected")
        if not expired_token_rejected:
            issues.append("Expired tokens are not properly rejected")
        
        print("❌ JWT token validation has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_conversation_generation():
    """Test conversation generation for quality and document creation"""
    global auth_token
    
    print("\n" + "="*80)
    print("TESTING CONVERSATION GENERATION AND DOCUMENT CREATION")
    print("="*80)
    
    # Ensure we have a valid token
    if not auth_token:
        print("❌ Cannot test conversation generation without a valid token")
        return False, "No valid token available"
    
    # Test 1: Create a new simulation
    print("\nTest 1: Creating a new simulation")
    
    simulation_start_test, simulation_start_response = run_test(
        "Start simulation",
        "/simulation/start",
        method="POST",
        auth=True,
        expected_keys=["message", "state"]
    )
    
    if not simulation_start_test:
        print("❌ Failed to start simulation")
        return False, "Failed to start simulation"
    
    print("✅ Successfully started simulation")
    
    # Test 2: Create test agents
    print("\nTest 2: Creating test agents")
    
    # Create three agents with different archetypes
    agent_data = [
        {
            "name": "Dr. James Wilson",
            "archetype": "scientist",
            "personality": {
                "extroversion": 4,
                "optimism": 6,
                "curiosity": 9,
                "cooperativeness": 7,
                "energy": 6
            },
            "goal": "Advance scientific understanding of the project",
            "expertise": "Quantum Physics",
            "background": "Former lead researcher at CERN",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Sarah Johnson",
            "archetype": "leader",
            "personality": {
                "extroversion": 9,
                "optimism": 8,
                "curiosity": 6,
                "cooperativeness": 8,
                "energy": 8
            },
            "goal": "Ensure project success and team coordination",
            "expertise": "Project Management",
            "background": "20 years experience in tech leadership",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Michael Chen",
            "archetype": "skeptic",
            "personality": {
                "extroversion": 4,
                "optimism": 3,
                "curiosity": 7,
                "cooperativeness": 5,
                "energy": 5
            },
            "goal": "Identify and mitigate project risks",
            "expertise": "Risk Assessment",
            "background": "Former security consultant",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        }
    ]
    
    created_agents = []
    
    for agent in agent_data:
        create_agent_test, create_agent_response = run_test(
            f"Create Agent: {agent['name']}",
            "/agents",
            method="POST",
            data=agent,
            auth=True,
            expected_keys=["id", "name"]
        )
        
        if create_agent_test and create_agent_response:
            print(f"✅ Created agent: {create_agent_response.get('name')} with ID: {create_agent_response.get('id')}")
            created_agents.append(create_agent_response)
        else:
            print(f"❌ Failed to create agent: {agent['name']}")
    
    if len(created_agents) < 3:
        print(f"❌ Failed to create all test agents. Only created {len(created_agents)} out of 3.")
        return False, "Failed to create all test agents"
    
    # Test 3: Set a scenario
    print("\nTest 3: Setting a scenario")
    
    scenario_data = {
        "scenario": "The team is discussing the budget allocation for a new quantum computing project with potential applications in cryptography.",
        "scenario_name": "Quantum Computing Budget"
    }
    
    set_scenario_test, set_scenario_response = run_test(
        "Set Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=scenario_data,
        auth=True,
        expected_keys=["message", "scenario"]
    )
    
    if not set_scenario_test:
        print("❌ Failed to set scenario")
        return False, "Failed to set scenario"
    
    print("✅ Successfully set scenario")
    
    # Test 4: Generate a conversation round
    print("\nTest 4: Generating a conversation round")
    
    generate_data = {
        "round_number": 1,
        "time_period": "Day 1 Morning",
        "scenario": scenario_data["scenario"],
        "scenario_name": scenario_data["scenario_name"]
    }
    
    generate_test, generate_response = run_test(
        "Generate Conversation Round",
        "/conversation/generate",
        method="POST",
        data=generate_data,
        auth=True,
        expected_keys=["id", "round_number", "messages"]
    )
    
    if not generate_test or not generate_response:
        print("❌ Failed to generate conversation round")
        return False, "Failed to generate conversation round"
    
    print("✅ Generated conversation round")
    
    # Print the messages for this round
    print("\nMessages in this round:")
    for msg in generate_response.get("messages", []):
        agent_name = msg.get("agent_name", "Unknown")
        message = msg.get("message", "")
        print(f"{agent_name}: {message[:100]}..." if len(message) > 100 else f"{agent_name}: {message}")
    
    # Test 5: Check for document creation
    print("\nTest 5: Checking for document creation")
    
    # Wait a moment for any background document creation
    time.sleep(2)
    
    # Get documents
    get_docs_test, get_docs_response = run_test(
        "Get Documents",
        "/documents",
        method="GET",
        auth=True
    )
    
    if not get_docs_test:
        print("❌ Failed to get documents")
        return False, "Failed to get documents"
    
    # Check if any documents were created
    doc_count = len(get_docs_response) if get_docs_response else 0
    print(f"Found {doc_count} documents")
    
    # Test 6: Generate a budget-focused conversation
    print("\nTest 6: Generating a budget-focused conversation")
    
    budget_scenario_data = {
        "scenario": "The team needs to allocate the project budget of $2 million across development (40%), marketing (30%), operations (20%), and contingency (10%).",
        "scenario_name": "Budget Allocation"
    }
    
    set_budget_scenario_test, set_budget_scenario_response = run_test(
        "Set Budget Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=budget_scenario_data,
        auth=True,
        expected_keys=["message", "scenario"]
    )
    
    if not set_budget_scenario_test:
        print("❌ Failed to set budget scenario")
        return False, "Failed to set budget scenario"
    
    print("✅ Successfully set budget scenario")
    
    # Generate a budget conversation
    budget_generate_data = {
        "round_number": 2,
        "time_period": "Day 1 Afternoon",
        "scenario": budget_scenario_data["scenario"],
        "scenario_name": budget_scenario_data["scenario_name"]
    }
    
    budget_generate_test, budget_generate_response = run_test(
        "Generate Budget Conversation",
        "/conversation/generate",
        method="POST",
        data=budget_generate_data,
        auth=True,
        expected_keys=["id", "round_number", "messages"]
    )
    
    if not budget_generate_test or not budget_generate_response:
        print("❌ Failed to generate budget conversation")
        return False, "Failed to generate budget conversation"
    
    print("✅ Generated budget conversation")
    
    # Print the messages for this round
    print("\nMessages in budget conversation:")
    for msg in budget_generate_response.get("messages", []):
        agent_name = msg.get("agent_name", "Unknown")
        message = msg.get("message", "")
        print(f"{agent_name}: {message[:100]}..." if len(message) > 100 else f"{agent_name}: {message}")
    
    # Test 7: Check for budget document creation
    print("\nTest 7: Checking for budget document creation")
    
    # Wait a moment for any background document creation
    time.sleep(2)
    
    # Get documents again
    get_docs_after_test, get_docs_after_response = run_test(
        "Get Documents After Budget Conversation",
        "/documents",
        method="GET",
        auth=True
    )
    
    if not get_docs_after_test:
        print("❌ Failed to get documents after budget conversation")
        return False, "Failed to get documents after budget conversation"
    
    # Check if any new documents were created
    doc_after_count = len(get_docs_after_response) if get_docs_after_response else 0
    print(f"Found {doc_after_count} documents (previously {doc_count})")
    
    new_docs = doc_after_count - doc_count
    if new_docs > 0:
        print(f"✅ {new_docs} new document(s) created after budget conversation")
        
        # Check the most recent document
        latest_doc = get_docs_after_response[0] if get_docs_after_response else None
        if latest_doc:
            doc_id = latest_doc.get("id")
            doc_title = latest_doc.get("metadata", {}).get("title", "Unknown")
            doc_category = latest_doc.get("metadata", {}).get("category", "Unknown")
            doc_content = latest_doc.get("content", "")
            
            print(f"\nLatest document: {doc_title} (Category: {doc_category})")
            print(f"Document ID: {doc_id}")
            
            # Check for HTML formatting
            has_html = "<html" in doc_content.lower() or "<div" in doc_content.lower() or "<h1" in doc_content.lower()
            if has_html:
                print("✅ Document has HTML formatting")
            else:
                print("❌ Document does not have HTML formatting")
            
            # Check for CSS styling
            has_css = "style=" in doc_content.lower() or "<style>" in doc_content.lower()
            if has_css:
                print("✅ Document has CSS styling")
            else:
                print("❌ Document does not have CSS styling")
            
            # Check for charts
            has_chart = "chart" in doc_content.lower() or "data:image" in doc_content.lower() or "<canvas" in doc_content.lower()
            if has_chart:
                print("✅ Document contains chart elements")
                
                # Check for base64 images
                base64_pattern = r'data:image\/[^;]+;base64,[a-zA-Z0-9+/]+'
                base64_matches = re.findall(base64_pattern, doc_content)
                if base64_matches:
                    print(f"✅ Document contains {len(base64_matches)} base64 encoded image(s)")
                else:
                    print("❌ Document does not contain base64 encoded images")
            else:
                print("❌ Document does not contain chart elements")
    else:
        print("❌ No new documents created after budget conversation")
    
    # Test 8: Generate a timeline-focused conversation
    print("\nTest 8: Generating a timeline-focused conversation")
    
    timeline_scenario_data = {
        "scenario": "The team needs to establish a timeline for the project: Month 1-2 Development, Month 3-4 Testing, Month 4-5 Beta, Month 6 Launch.",
        "scenario_name": "Project Timeline"
    }
    
    set_timeline_scenario_test, set_timeline_scenario_response = run_test(
        "Set Timeline Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=timeline_scenario_data,
        auth=True,
        expected_keys=["message", "scenario"]
    )
    
    if not set_timeline_scenario_test:
        print("❌ Failed to set timeline scenario")
        return False, "Failed to set timeline scenario"
    
    print("✅ Successfully set timeline scenario")
    
    # Generate a timeline conversation
    timeline_generate_data = {
        "round_number": 3,
        "time_period": "Day 1 Evening",
        "scenario": timeline_scenario_data["scenario"],
        "scenario_name": timeline_scenario_data["scenario_name"]
    }
    
    timeline_generate_test, timeline_generate_response = run_test(
        "Generate Timeline Conversation",
        "/conversation/generate",
        method="POST",
        data=timeline_generate_data,
        auth=True,
        expected_keys=["id", "round_number", "messages"]
    )
    
    if not timeline_generate_test or not timeline_generate_response:
        print("❌ Failed to generate timeline conversation")
        return False, "Failed to generate timeline conversation"
    
    print("✅ Generated timeline conversation")
    
    # Test 9: Check for timeline document creation
    print("\nTest 9: Checking for timeline document creation")
    
    # Wait a moment for any background document creation
    time.sleep(2)
    
    # Get documents again
    get_docs_timeline_test, get_docs_timeline_response = run_test(
        "Get Documents After Timeline Conversation",
        "/documents",
        method="GET",
        auth=True
    )
    
    if not get_docs_timeline_test:
        print("❌ Failed to get documents after timeline conversation")
        return False, "Failed to get documents after timeline conversation"
    
    # Check if any new documents were created
    doc_timeline_count = len(get_docs_timeline_response) if get_docs_timeline_response else 0
    print(f"Found {doc_timeline_count} documents (previously {doc_after_count})")
    
    new_timeline_docs = doc_timeline_count - doc_after_count
    if new_timeline_docs > 0:
        print(f"✅ {new_timeline_docs} new document(s) created after timeline conversation")
        
        # Check the most recent document
        latest_doc = get_docs_timeline_response[0] if get_docs_timeline_response else None
        if latest_doc:
            doc_id = latest_doc.get("id")
            doc_title = latest_doc.get("metadata", {}).get("title", "Unknown")
            doc_category = latest_doc.get("metadata", {}).get("category", "Unknown")
            doc_content = latest_doc.get("content", "")
            
            print(f"\nLatest document: {doc_title} (Category: {doc_category})")
            print(f"Document ID: {doc_id}")
            
            # Check for timeline chart
            has_timeline = "timeline" in doc_content.lower() or "gantt" in doc_content.lower()
            if has_timeline:
                print("✅ Document contains timeline elements")
            else:
                print("❌ Document does not contain timeline elements")
    else:
        print("❌ No new documents created after timeline conversation")
    
    # Test 10: Generate a risk assessment conversation
    print("\nTest 10: Generating a risk assessment conversation")
    
    risk_scenario_data = {
        "scenario": "The team needs to assess project risks: technical complexity (7/10), market competition (8/10), and regulatory challenges (6/10).",
        "scenario_name": "Risk Assessment"
    }
    
    set_risk_scenario_test, set_risk_scenario_response = run_test(
        "Set Risk Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=risk_scenario_data,
        auth=True,
        expected_keys=["message", "scenario"]
    )
    
    if not set_risk_scenario_test:
        print("❌ Failed to set risk scenario")
        return False, "Failed to set risk scenario"
    
    print("✅ Successfully set risk scenario")
    
    # Generate a risk assessment conversation
    risk_generate_data = {
        "round_number": 4,
        "time_period": "Day 2 Morning",
        "scenario": risk_scenario_data["scenario"],
        "scenario_name": risk_scenario_data["scenario_name"]
    }
    
    risk_generate_test, risk_generate_response = run_test(
        "Generate Risk Assessment Conversation",
        "/conversation/generate",
        method="POST",
        data=risk_generate_data,
        auth=True,
        expected_keys=["id", "round_number", "messages"]
    )
    
    if not risk_generate_test or not risk_generate_response:
        print("❌ Failed to generate risk assessment conversation")
        return False, "Failed to generate risk assessment conversation"
    
    print("✅ Generated risk assessment conversation")
    
    # Test 11: Check for risk assessment document creation
    print("\nTest 11: Checking for risk assessment document creation")
    
    # Wait a moment for any background document creation
    time.sleep(2)
    
    # Get documents again
    get_docs_risk_test, get_docs_risk_response = run_test(
        "Get Documents After Risk Assessment Conversation",
        "/documents",
        method="GET",
        auth=True
    )
    
    if not get_docs_risk_test:
        print("❌ Failed to get documents after risk assessment conversation")
        return False, "Failed to get documents after risk assessment conversation"
    
    # Check if any new documents were created
    doc_risk_count = len(get_docs_risk_response) if get_docs_risk_response else 0
    print(f"Found {doc_risk_count} documents (previously {doc_timeline_count})")
    
    new_risk_docs = doc_risk_count - doc_timeline_count
    if new_risk_docs > 0:
        print(f"✅ {new_risk_docs} new document(s) created after risk assessment conversation")
        
        # Check the most recent document
        latest_doc = get_docs_risk_response[0] if get_docs_risk_response else None
        if latest_doc:
            doc_id = latest_doc.get("id")
            doc_title = latest_doc.get("metadata", {}).get("title", "Unknown")
            doc_category = latest_doc.get("metadata", {}).get("category", "Unknown")
            doc_content = latest_doc.get("content", "")
            
            print(f"\nLatest document: {doc_title} (Category: {doc_category})")
            print(f"Document ID: {doc_id}")
            
            # Check for risk assessment chart
            has_risk_chart = "risk" in doc_content.lower() and ("chart" in doc_content.lower() or "data:image" in doc_content.lower())
            if has_risk_chart:
                print("✅ Document contains risk assessment chart elements")
            else:
                print("❌ Document does not contain risk assessment chart elements")
    else:
        print("❌ No new documents created after risk assessment conversation")
    
    # Print summary
    print("\nCONVERSATION GENERATION AND DOCUMENT CREATION SUMMARY:")
    
    # Check if all critical tests passed
    conversation_works = generate_test and budget_generate_test and timeline_generate_test and risk_generate_test
    document_creation_works = new_docs > 0 or new_timeline_docs > 0 or new_risk_docs > 0
    
    if conversation_works and document_creation_works:
        print("✅ Conversation generation and document creation are working correctly!")
        print("✅ Conversations are generated successfully")
        print("✅ Documents are created based on conversation content")
        
        total_new_docs = new_docs + new_timeline_docs + new_risk_docs
        print(f"✅ {total_new_docs} total documents created from conversations")
        
        return True, "Conversation generation and document creation are working correctly"
    else:
        issues = []
        if not conversation_works:
            issues.append("Conversation generation is not functioning properly")
        if not document_creation_works:
            issues.append("Document creation is not functioning properly")
        
        print("❌ Conversation generation and document creation have issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_conversation_quality():
    """Test conversation quality for natural dialogue and solution focus"""
    global auth_token
    
    print("\n" + "="*80)
    print("TESTING CONVERSATION QUALITY")
    print("="*80)
    
    # Ensure we have a valid token
    if not auth_token:
        print("❌ Cannot test conversation quality without a valid token")
        return False, "No valid token available"
    
    # Test 1: Create a new simulation
    print("\nTest 1: Creating a new simulation")
    
    simulation_start_test, simulation_start_response = run_test(
        "Start simulation",
        "/simulation/start",
        method="POST",
        auth=True,
        expected_keys=["message", "state"]
    )
    
    if not simulation_start_test:
        print("❌ Failed to start simulation")
        return False, "Failed to start simulation"
    
    print("✅ Successfully started simulation")
    
    # Test 2: Create test agents
    print("\nTest 2: Creating test agents")
    
    # Create agents with different expertise areas
    agent_data = [
        {
            "name": "Dr. James Wilson",
            "archetype": "scientist",
            "personality": {
                "extroversion": 4,
                "optimism": 6,
                "curiosity": 9,
                "cooperativeness": 7,
                "energy": 6
            },
            "goal": "Advance scientific understanding of quantum computing",
            "expertise": "Quantum Physics",
            "background": "Former lead researcher at CERN with 15 years experience in quantum computing",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Sarah Johnson",
            "archetype": "leader",
            "personality": {
                "extroversion": 9,
                "optimism": 8,
                "curiosity": 6,
                "cooperativeness": 8,
                "energy": 8
            },
            "goal": "Ensure project success and team coordination",
            "expertise": "Project Management",
            "background": "20 years experience in tech leadership and managing complex technical projects",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Michael Chen",
            "archetype": "skeptic",
            "personality": {
                "extroversion": 4,
                "optimism": 3,
                "curiosity": 7,
                "cooperativeness": 5,
                "energy": 5
            },
            "goal": "Identify and mitigate project risks",
            "expertise": "Risk Assessment",
            "background": "Former security consultant specializing in cryptographic systems",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        }
    ]
    
    created_agents = []
    
    for agent in agent_data:
        create_agent_test, create_agent_response = run_test(
            f"Create Agent: {agent['name']}",
            "/agents",
            method="POST",
            data=agent,
            auth=True,
            expected_keys=["id", "name"]
        )
        
        if create_agent_test and create_agent_response:
            print(f"✅ Created agent: {create_agent_response.get('name')} with ID: {create_agent_response.get('id')}")
            created_agents.append(create_agent_response)
        else:
            print(f"❌ Failed to create agent: {agent['name']}")
    
    if len(created_agents) < 3:
        print(f"❌ Failed to create enough test agents. Only created {len(created_agents)} out of 3.")
        return False, "Failed to create enough test agents"
    
    # Test 3: Set a scenario
    print("\nTest 3: Setting a scenario")
    
    scenario_data = {
        "scenario": "The team is discussing the implementation of a new quantum computing project with potential applications in cryptography. The project has a tight deadline and limited budget, but could revolutionize secure communications if successful.",
        "scenario_name": "Quantum Cryptography Project"
    }
    
    set_scenario_test, set_scenario_response = run_test(
        "Set Scenario",
        "/simulation/set-scenario",
        method="POST",
        data=scenario_data,
        auth=True,
        expected_keys=["message", "scenario"]
    )
    
    if not set_scenario_test:
        print("❌ Failed to set scenario")
        return False, "Failed to set scenario"
    
    print("✅ Successfully set scenario")
    
    # Test 4: Generate multiple conversation rounds
    print("\nTest 4: Generating multiple conversation rounds")
    
    # Store all conversation rounds for analysis
    conversation_rounds = []
    
    # Generate 3 conversation rounds
    for i in range(3):
        print(f"\nGenerating conversation round {i+1}/3:")
        
        generate_data = {
            "round_number": i+1,
            "time_period": f"Day {i//3 + 1} {'Morning' if i%3==0 else 'Afternoon' if i%3==1 else 'Evening'}",
            "scenario": scenario_data["scenario"],
            "scenario_name": scenario_data["scenario_name"]
        }
        
        generate_test, generate_response = run_test(
            f"Generate Conversation Round {i+1}",
            "/conversation/generate",
            method="POST",
            data=generate_data,
            auth=True,
            expected_keys=["id", "round_number", "messages"]
        )
        
        if generate_test and generate_response:
            print(f"✅ Generated conversation round {i+1}")
            conversation_rounds.append(generate_response)
            
            # Print the messages for this round
            print("\nMessages in this round:")
            for msg in generate_response.get("messages", []):
                agent_name = msg.get("agent_name", "Unknown")
                message = msg.get("message", "")
                print(f"{agent_name}: {message[:100]}..." if len(message) > 100 else f"{agent_name}: {message}")
        else:
            print(f"❌ Failed to generate conversation round {i+1}")
    
    if len(conversation_rounds) < 2:
        print(f"❌ Failed to generate enough conversation rounds. Only generated {len(conversation_rounds)} out of 3.")
        return False, "Failed to generate enough conversation rounds"
    
    # Test 5: Check for background phrase repetition
    print("\nTest 5: Checking for background phrase repetition")
    
    # Define patterns for background phrases
    background_phrases = [
        r"as an? (expert|specialist|professional) in",
        r"given my (background|experience|expertise|knowledge|training) in",
        r"from my (experience|perspective|background|expertise|viewpoint) in",
        r"based on my (\d+|several|many|extensive|years of) (years|experience)",
        r"speaking as an? (expert|specialist|professional|authority|leader)",
        r"as someone (who|with) (has|have|having)",
        r"with my (expertise|experience|background|knowledge|training) in",
        r"given my professional (experience|background|expertise|knowledge)",
        r"in my (field|profession|discipline|area of expertise)",
        r"as a (quantum physicist|project manager|risk analyst|business developer)"
    ]
    
    # Count background mentions by round
    background_mentions_by_round = [0] * len(conversation_rounds)
    background_mention_examples = []
    
    for round_idx, round_data in enumerate(conversation_rounds):
        for message in round_data.get("messages", []):
            agent_name = message.get("agent_name", "Unknown")
            message_text = message.get("message", "")
            
            for pattern in background_phrases:
                matches = re.finditer(pattern, message_text.lower())
                for match in matches:
                    background_mentions_by_round[round_idx] = background_mentions_by_round[round_idx] + 1
                    background_mention_examples.append({
                        "round": round_idx + 1,
                        "agent": agent_name,
                        "pattern": pattern,
                        "text": message_text[max(0, match.start() - 20):min(len(message_text), match.end() + 20)]
                    })
    
    # Print background mention statistics
    print("\nBackground mentions by round:")
    for i, count in enumerate(background_mentions_by_round):
        print(f"Round {i+1}: {count} mentions")
    
    if background_mention_examples:
        print("\nExamples of background mentions:")
        for example in background_mention_examples[:3]:  # Show up to 3 examples
            print(f"Round {example['round']}, {example['agent']}: \"...{example['text']}...\"")
    
    total_background_mentions = sum(background_mentions_by_round)
    total_messages = sum(len(round_data.get("messages", [])) for round_data in conversation_rounds)
    background_mention_percentage = (total_background_mentions / total_messages) * 100 if total_messages > 0 else 0
    
    print(f"\nTotal background mentions: {total_background_mentions}/{total_messages} messages ({background_mention_percentage:.1f}%)")
    
    if background_mention_percentage <= 10:
        print("✅ Agents rarely mention their background explicitly")
    else:
        print("❌ Agents frequently mention their background explicitly")
    
    # Test 6: Check for solution-focused responses
    print("\nTest 6: Checking for solution-focused responses")
    
    # Define solution-focused phrases
    solution_phrases = [
        "suggest", "recommend", "propose", "implement", 
        "approach", "solution", "strategy", "plan",
        "timeline", "schedule", "milestone", "next steps"
    ]
    
    # Count solution-focused messages
    solution_focused_count = 0
    
    for round_data in conversation_rounds:
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for phrase in solution_phrases:
                if phrase in message_text:
                    solution_focused_count += 1
                    break
    
    solution_percentage = (solution_focused_count / total_messages) * 100 if total_messages > 0 else 0
    print(f"Solution-focused messages: {solution_focused_count}/{total_messages} ({solution_percentage:.1f}%)")
    
    if solution_percentage >= 50:
        print("✅ Conversations are solution-focused")
    else:
        print("❌ Conversations are not sufficiently solution-focused")
    
    # Test 7: Check for natural conversation flow
    print("\nTest 7: Checking for natural conversation flow")
    
    # Define patterns for natural conversation flow
    natural_flow_patterns = [
        r"(agree|concur) with (.*?)(point|assessment|analysis|suggestion|recommendation)",
        r"(building|expanding) on (.*?)(point|idea|suggestion|thought)",
        r"(to add to|following up on) what (.*?) (said|mentioned|suggested|pointed out)",
        r"(as|like) (.*?) (mentioned|pointed out|suggested|said)",
        r"(good|excellent|interesting|valid) point(.*?)"
    ]
    
    # Count natural flow patterns
    natural_flow_count = 0
    natural_flow_examples = []
    
    for round_idx, round_data in enumerate(conversation_rounds):
        messages = round_data.get("messages", [])
        for i, message in enumerate(messages):
            if i == 0:  # Skip first message in each round
                continue
                
            message_text = message.get("message", "")
            agent_name = message.get("agent_name", "Unknown")
            
            for pattern in natural_flow_patterns:
                matches = re.search(pattern, message_text.lower())
                if matches:
                    natural_flow_count += 1
                    natural_flow_examples.append({
                        "round": round_idx + 1,
                        "agent": agent_name,
                        "text": message_text[:150] + "..." if len(message_text) > 150 else message_text
                    })
                    break
    
    # Print natural flow statistics
    natural_flow_percentage = (natural_flow_count / (total_messages - len(conversation_rounds))) * 100 if (total_messages - len(conversation_rounds)) > 0 else 0
    print(f"Natural conversation flow: {natural_flow_count}/{total_messages - len(conversation_rounds)} messages ({natural_flow_percentage:.1f}%)")
    
    if natural_flow_examples:
        print("\nExamples of natural conversation flow:")
        for example in natural_flow_examples[:3]:  # Show up to 3 examples
            print(f"Round {example['round']}, {example['agent']}: \"{example['text']}\"")
    
    if natural_flow_percentage >= 30:
        print("✅ Conversations show natural flow")
    else:
        print("❌ Conversations lack natural flow")
    
    # Print summary
    print("\nCONVERSATION QUALITY SUMMARY:")
    
    # Check if all critical tests passed
    low_background_mentions = background_mention_percentage <= 10
    is_solution_focused = solution_percentage >= 50
    has_natural_flow = natural_flow_percentage >= 30
    
    if low_background_mentions and is_solution_focused and has_natural_flow:
        print("✅ Conversation quality is good!")
        print("✅ Agents don't repeat background phrases")
        print("✅ Conversations are solution-focused")
        print("✅ Conversations have natural flow")
        return True, "Conversation quality is good"
    else:
        issues = []
        if not low_background_mentions:
            issues.append(f"Agents mention their background in {background_mention_percentage:.1f}% of messages (target: ≤10%)")
        if not is_solution_focused:
            issues.append(f"Only {solution_percentage:.1f}% of messages are solution-focused (target: ≥50%)")
        if not has_natural_flow:
            issues.append(f"Only {natural_flow_percentage:.1f}% of messages show natural flow (target: ≥30%)")
        
        print("❌ Conversation quality has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def test_random_scenario_generation():
    """Test the random scenario generation for detailed scenarios"""
    global auth_token
    
    print("\n" + "="*80)
    print("TESTING RANDOM SCENARIO GENERATION")
    print("="*80)
    
    # Ensure we have a valid token
    if not auth_token:
        print("❌ Cannot test random scenario generation without a valid token")
        return False, "No valid token available"
    
    # Test 1: Get random scenario
    print("\nTest 1: Getting a random scenario")
    
    random_scenario_test, random_scenario_response = run_test(
        "Get Random Scenario",
        "/simulation/random-scenario",
        method="GET",
        auth=True,
        expected_keys=["scenario", "scenario_name"]
    )
    
    if not random_scenario_test or not random_scenario_response:
        print("❌ Failed to get random scenario")
        return False, "Failed to get random scenario"
    
    print("✅ Successfully got random scenario")
    
    # Analyze scenario content
    scenario_text = random_scenario_response.get("scenario", "")
    scenario_name = random_scenario_response.get("scenario_name", "")
    
    print(f"\nScenario Name: {scenario_name}")
    print(f"Scenario Length: {len(scenario_text)} characters")
    print(f"Scenario Preview: {scenario_text[:200]}...")
    
    # Check scenario length
    if len(scenario_text) >= 500:
        print("✅ Scenario is detailed (500+ characters)")
    else:
        print("❌ Scenario is not detailed enough (< 500 characters)")
    
    # Check for specific details
    has_company_names = re.search(r'(Inc\.|Corp\.|Corporation|Company|Technologies|Systems|Labs)', scenario_text) is not None
    has_numbers = re.search(r'\d+(\.\d+)?\s*(million|billion|thousand|percent|%)', scenario_text) is not None
    has_timeline = re.search(r'(days|weeks|months|years|hours|minutes)', scenario_text) is not None
    
    if has_company_names:
        print("✅ Scenario includes specific company names")
    else:
        print("❌ Scenario lacks specific company names")
    
    if has_numbers:
        print("✅ Scenario includes concrete numbers and metrics")
    else:
        print("❌ Scenario lacks concrete numbers and metrics")
    
    if has_timeline:
        print("✅ Scenario includes timeline information")
    else:
        print("❌ Scenario lacks timeline information")
    
    # Test 2: Get multiple random scenarios to check variety
    print("\nTest 2: Getting multiple random scenarios to check variety")
    
    scenarios = []
    
    for i in range(3):
        random_scenario_test, random_scenario_response = run_test(
            f"Get Random Scenario {i+1}",
            "/simulation/random-scenario",
            method="GET",
            auth=True,
            expected_keys=["scenario", "scenario_name"]
        )
        
        if random_scenario_test and random_scenario_response:
            scenarios.append(random_scenario_response)
    
    # Check for variety in scenarios
    if len(scenarios) >= 2:
        scenario_texts = [s.get("scenario", "") for s in scenarios]
        scenario_names = [s.get("scenario_name", "") for s in scenarios]
        
        # Check if scenarios are different
        unique_scenarios = len(set(scenario_texts))
        unique_names = len(set(scenario_names))
        
        print(f"\nUnique scenarios: {unique_scenarios}/{len(scenarios)}")
        print(f"Unique scenario names: {unique_names}/{len(scenarios)}")
        
        if unique_scenarios == len(scenarios):
            print("✅ All scenarios are unique")
        else:
            print("❌ Some scenarios are duplicates")
    
    # Print summary
    print("\nRANDOM SCENARIO GENERATION SUMMARY:")
    
    # Check if all critical tests passed
    is_detailed = len(scenario_text) >= 500
    has_specific_details = has_company_names and has_numbers and has_timeline
    has_variety = len(scenarios) >= 2 and unique_scenarios == len(scenarios)
    
    if is_detailed and has_specific_details and has_variety:
        print("✅ Random scenario generation is working correctly!")
        print("✅ Scenarios are detailed (500+ characters)")
        print("✅ Scenarios include specific details (company names, numbers, timelines)")
        print("✅ Scenarios have good variety")
        return True, "Random scenario generation is working correctly"
    else:
        issues = []
        if not is_detailed:
            issues.append("Scenarios are not detailed enough (< 500 characters)")
        if not has_specific_details:
            missing = []
            if not has_company_names:
                missing.append("company names")
            if not has_numbers:
                missing.append("concrete numbers")
            if not has_timeline:
                missing.append("timeline information")
            issues.append(f"Scenarios lack specific details ({', '.join(missing)})")
        if not has_variety:
            issues.append("Scenarios lack variety")
        
        print("❌ Random scenario generation has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

def main():
    """Main function to run all tests"""
    # Test email/password login
    email_password_login_result, email_password_login_details = test_email_password_login()
    
    # Test guest login
    guest_login_result, guest_login_details = test_guest_login()
    
    # Test JWT validation
    jwt_validation_result, jwt_validation_details = test_jwt_validation()
    
    # Test conversation generation and document creation
    conversation_result, conversation_details = test_conversation_generation()
    
    # Test conversation quality
    quality_result, quality_details = test_conversation_quality()
    
    # Test random scenario generation
    scenario_result, scenario_details = test_random_scenario_generation()
    
    # Print overall summary
    print("\n" + "="*80)
    print("OVERALL TEST SUMMARY")
    print("="*80)
    
    print(f"Email/Password Login: {'✅ PASSED' if email_password_login_result else '❌ FAILED'}")
    print(f"Guest Login: {'✅ PASSED' if guest_login_result else '❌ FAILED'}")
    print(f"JWT Validation: {'✅ PASSED' if jwt_validation_result else '❌ FAILED'}")
    print(f"Conversation Generation & Document Creation: {'✅ PASSED' if conversation_result else '❌ FAILED'}")
    print(f"Conversation Quality: {'✅ PASSED' if quality_result else '❌ FAILED'}")
    print(f"Random Scenario Generation: {'✅ PASSED' if scenario_result else '❌ FAILED'}")
    
    print("\nDetailed test results:")
    print_summary()

if __name__ == "__main__":
    main()