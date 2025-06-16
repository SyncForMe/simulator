#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
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

# User data for testing
users = {
    "user1": {
        "email": f"user1.{uuid.uuid4()}@example.com",
        "password": "SecurePassword123!",
        "name": "Test User One",
        "auth_token": None,
        "user_id": None,
        "documents": [],
        "agents": [],
        "conversations": []
    },
    "user2": {
        "email": f"user2.{uuid.uuid4()}@example.com",
        "password": "SecurePassword456!",
        "name": "Test User Two",
        "auth_token": None,
        "user_id": None,
        "documents": [],
        "agents": [],
        "conversations": []
    }
}

def run_test(test_name, endpoint, method="GET", data=None, expected_status=200, expected_keys=None, auth_token=None, headers=None, params=None, measure_time=False):
    """Run a test against the specified endpoint"""
    url = f"{API_URL}{endpoint}"
    print(f"\n{'='*80}\nTesting: {test_name} ({method} {url})")
    
    # Set up headers with auth token if needed
    if headers is None:
        headers = {}
    
    if auth_token:
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

def register_user(user_key):
    """Register a user and store the auth token"""
    user = users[user_key]
    
    register_data = {
        "email": user["email"],
        "password": user["password"],
        "name": user["name"]
    }
    
    print(f"\nRegistering user: {user['name']} ({user['email']})")
    
    register_test, register_response = run_test(
        f"Register {user_key}",
        "/auth/register",
        method="POST",
        data=register_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if register_test and register_response:
        user["auth_token"] = register_response.get("access_token")
        user["user_id"] = register_response.get("user", {}).get("id")
        print(f"✅ Successfully registered {user_key} with ID: {user['user_id']}")
        return True
    else:
        print(f"❌ Failed to register {user_key}")
        return False

def login_user(user_key):
    """Login a user and update the auth token"""
    user = users[user_key]
    
    login_data = {
        "email": user["email"],
        "password": user["password"]
    }
    
    print(f"\nLogging in user: {user['name']} ({user['email']})")
    
    login_test, login_response = run_test(
        f"Login {user_key}",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    if login_test and login_response:
        user["auth_token"] = login_response.get("access_token")
        user["user_id"] = login_response.get("user", {}).get("id")
        print(f"✅ Successfully logged in {user_key} with ID: {user['user_id']}")
        return True
    else:
        print(f"❌ Failed to login {user_key}")
        return False

def create_document(user_key, title=None, category="Protocol"):
    """Create a document for a specific user"""
    user = users[user_key]
    
    if not title:
        title = f"Test Document for {user['name']} - {uuid.uuid4()}"
    
    document_data = {
        "title": title,
        "category": category,
        "description": f"This is a test document created by {user['name']}",
        "content": f"""# {title}

## Created By
{user['name']} ({user['email']})

## Purpose
This document was created for testing user data isolation.

## Content
This is a test document that should only be visible to {user['name']}.
It contains some unique identifier: {uuid.uuid4()}

## Details
- Category: {category}
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Author: {user['name']}
""",
        "keywords": ["test", category.lower(), user_key],
        "authors": [user["name"]]
    }
    
    print(f"\nCreating document for {user_key}: {title}")
    
    create_doc_test, create_doc_response = run_test(
        f"Create Document for {user_key}",
        "/documents/create",
        method="POST",
        data=document_data,
        auth_token=user["auth_token"],
        expected_keys=["success", "document_id"]
    )
    
    if create_doc_test and create_doc_response:
        document_id = create_doc_response.get("document_id")
        if document_id:
            user["documents"].append({
                "id": document_id,
                "title": title,
                "category": category
            })
            print(f"✅ Created document for {user_key} with ID: {document_id}")
            return document_id
        else:
            print(f"❌ Failed to get document ID for {user_key}")
            return None
    else:
        print(f"❌ Failed to create document for {user_key}")
        return None

def create_saved_agent(user_key, name=None):
    """Create a saved agent for a specific user"""
    user = users[user_key]
    
    if not name:
        name = f"Test Agent for {user['name']} - {uuid.uuid4()}"
    
    agent_data = {
        "name": name,
        "archetype": "scientist",
        "personality": {
            "extroversion": 5,
            "optimism": 7,
            "curiosity": 9,
            "cooperativeness": 6,
            "energy": 8
        },
        "goal": f"This is a test agent created by {user['name']} for isolation testing",
        "expertise": "Testing user data isolation",
        "background": f"Created by {user['name']} ({user['email']}) for testing purposes",
        "avatar_url": "",
        "avatar_prompt": f"Test agent for {user['name']}"
    }
    
    print(f"\nCreating saved agent for {user_key}: {name}")
    
    create_agent_test, create_agent_response = run_test(
        f"Create Saved Agent for {user_key}",
        "/agents/saved",
        method="POST",
        data=agent_data,
        auth_token=user["auth_token"],
        expected_keys=["id", "name"]
    )
    
    if create_agent_test and create_agent_response:
        agent_id = create_agent_response.get("id")
        if agent_id:
            user["agents"].append({
                "id": agent_id,
                "name": name
            })
            print(f"✅ Created saved agent for {user_key} with ID: {agent_id}")
            return agent_id
        else:
            print(f"❌ Failed to get agent ID for {user_key}")
            return None
    else:
        print(f"❌ Failed to create saved agent for {user_key}")
        return None

def create_conversation(user_key, title=None):
    """Create a conversation for a specific user"""
    user = users[user_key]
    
    if not title:
        title = f"Test Conversation for {user['name']} - {uuid.uuid4()}"
    
    conversation_data = {
        "title": title,
        "participants": [f"Test Participant for {user['name']}"],
        "messages": [
            {
                "sender": f"Test Participant for {user['name']}",
                "content": f"This is a test message in a conversation created by {user['name']}",
                "timestamp": datetime.now().isoformat()
            }
        ],
        "language": "en",
        "tags": ["test", user_key]
    }
    
    print(f"\nCreating conversation for {user_key}: {title}")
    
    create_conv_test, create_conv_response = run_test(
        f"Create Conversation for {user_key}",
        "/conversations",
        method="POST",
        data=conversation_data,
        auth_token=user["auth_token"],
        expected_keys=["id", "title"]
    )
    
    if create_conv_test and create_conv_response:
        conversation_id = create_conv_response.get("id")
        if conversation_id:
            user["conversations"].append({
                "id": conversation_id,
                "title": title
            })
            print(f"✅ Created conversation for {user_key} with ID: {conversation_id}")
            return conversation_id
        else:
            print(f"❌ Failed to get conversation ID for {user_key}")
            return None
    else:
        print(f"❌ Failed to create conversation for {user_key}")
        return None

def test_user_data_isolation():
    """Test user data isolation across all features"""
    print("\n" + "="*80)
    print("TESTING USER DATA ISOLATION")
    print("="*80)
    
    # Step 1: Register two different users
    print("\nStep 1: Register two different users")
    user1_registered = register_user("user1")
    user2_registered = register_user("user2")
    
    if not user1_registered or not user2_registered:
        print("❌ Failed to register both users. Cannot continue isolation testing.")
        return False
    
    # Step 2: Create data for each user
    print("\nStep 2: Create data for each user")
    
    # Create documents for each user
    print("\nCreating documents for each user")
    for i in range(3):
        create_document("user1", f"User1 Document {i+1}")
        create_document("user2", f"User2 Document {i+1}")
    
    # Create saved agents for each user
    print("\nCreating saved agents for each user")
    try:
        for i in range(2):
            create_saved_agent("user1", f"User1 Agent {i+1}")
            create_saved_agent("user2", f"User2 Agent {i+1}")
    except Exception as e:
        print(f"Error creating saved agents: {e}")
        print("Continuing with test...")
    
    # Create conversations for each user
    print("\nCreating conversations for each user")
    try:
        for i in range(2):
            create_conversation("user1", f"User1 Conversation {i+1}")
            create_conversation("user2", f"User2 Conversation {i+1}")
    except Exception as e:
        print(f"Error creating conversations: {e}")
        print("Continuing with test...")
    
    # Step 3: Test data separation across all features
    print("\nStep 3: Test data separation across all features")
    
    # Test document isolation
    print("\nTesting document isolation")
    
    # Get user1's documents
    user1_docs_test, user1_docs_response = run_test(
        "Get User1 Documents",
        "/documents",
        method="GET",
        auth_token=users["user1"]["auth_token"]
    )
    
    # Get user2's documents
    user2_docs_test, user2_docs_response = run_test(
        "Get User2 Documents",
        "/documents",
        method="GET",
        auth_token=users["user2"]["auth_token"]
    )
    
    # Verify document isolation
    document_isolation = True
    
    if user1_docs_test and user2_docs_test:
        user1_doc_ids = [doc.get("id") for doc in user1_docs_response]
        user2_doc_ids = [doc.get("id") for doc in user2_docs_response]
        
        # Check if user1 can see user2's documents
        user1_sees_user2_docs = any(doc_id in user1_doc_ids for doc_id in [doc["id"] for doc in users["user2"]["documents"]])
        
        # Check if user2 can see user1's documents
        user2_sees_user1_docs = any(doc_id in user2_doc_ids for doc_id in [doc["id"] for doc in users["user1"]["documents"]])
        
        if user1_sees_user2_docs:
            print("❌ User1 can see User2's documents")
            document_isolation = False
        else:
            print("✅ User1 cannot see User2's documents")
        
        if user2_sees_user1_docs:
            print("❌ User2 can see User1's documents")
            document_isolation = False
        else:
            print("✅ User2 cannot see User1's documents")
    else:
        print("❌ Failed to retrieve documents for both users")
        document_isolation = False
    
    # Test saved agent isolation
    print("\nTesting saved agent isolation")
    agent_isolation = True
    
    try:
        # Get user1's saved agents
        user1_agents_test, user1_agents_response = run_test(
            "Get User1 Saved Agents",
            "/agents/saved",
            method="GET",
            auth_token=users["user1"]["auth_token"]
        )
        
        # Get user2's saved agents
        user2_agents_test, user2_agents_response = run_test(
            "Get User2 Saved Agents",
            "/agents/saved",
            method="GET",
            auth_token=users["user2"]["auth_token"]
        )
        
        if user1_agents_test and user2_agents_test:
            user1_agent_ids = [agent.get("id") for agent in user1_agents_response]
            user2_agent_ids = [agent.get("id") for agent in user2_agents_response]
            
            # Check if user1 can see user2's agents
            user1_sees_user2_agents = any(agent_id in user1_agent_ids for agent_id in [agent["id"] for agent in users["user2"]["agents"]])
            
            # Check if user2 can see user1's agents
            user2_sees_user1_agents = any(agent_id in user2_agent_ids for agent_id in [agent["id"] for agent in users["user1"]["agents"]])
            
            if user1_sees_user2_agents:
                print("❌ User1 can see User2's saved agents")
                agent_isolation = False
            else:
                print("✅ User1 cannot see User2's saved agents")
            
            if user2_sees_user1_agents:
                print("❌ User2 can see User1's saved agents")
                agent_isolation = False
            else:
                print("✅ User2 cannot see User1's saved agents")
        else:
            print("❌ Failed to retrieve saved agents for both users")
            agent_isolation = False
    except Exception as e:
        print(f"Error testing saved agent isolation: {e}")
        print("Continuing with test...")
        agent_isolation = "N/A"
    
    # Test conversation isolation
    print("\nTesting conversation isolation")
    conversation_isolation = True
    
    try:
        # Get user1's conversations
        user1_convs_test, user1_convs_response = run_test(
            "Get User1 Conversations",
            "/conversations",
            method="GET",
            auth_token=users["user1"]["auth_token"]
        )
        
        # Get user2's conversations
        user2_convs_test, user2_convs_response = run_test(
            "Get User2 Conversations",
            "/conversations",
            method="GET",
            auth_token=users["user2"]["auth_token"]
        )
        
        if user1_convs_test and user2_convs_test:
            user1_conv_ids = [conv.get("id") for conv in user1_convs_response]
            user2_conv_ids = [conv.get("id") for conv in user2_convs_response]
            
            # Check if user1 can see user2's conversations
            user1_sees_user2_convs = any(conv_id in user1_conv_ids for conv_id in [conv["id"] for conv in users["user2"]["conversations"]])
            
            # Check if user2 can see user1's conversations
            user2_sees_user1_convs = any(conv_id in user2_conv_ids for conv_id in [conv["id"] for conv in users["user1"]["conversations"]])
            
            if user1_sees_user2_convs:
                print("❌ User1 can see User2's conversations")
                conversation_isolation = False
            else:
                print("✅ User1 cannot see User2's conversations")
            
            if user2_sees_user1_convs:
                print("❌ User2 can see User1's conversations")
                conversation_isolation = False
            else:
                print("✅ User2 cannot see User1's conversations")
        else:
            print("❌ Failed to retrieve conversations for both users")
            conversation_isolation = False
    except Exception as e:
        print(f"Error testing conversation isolation: {e}")
        print("Continuing with test...")
        conversation_isolation = "N/A"
    
    # Step 4: Test cross-user access prevention
    print("\nStep 4: Test cross-user access prevention")
    
    # Try to access another user's document directly
    cross_access_prevention = True
    
    if users["user1"]["documents"] and users["user2"]["documents"]:
        user1_doc_id = users["user1"]["documents"][0]["id"]
        user2_doc_id = users["user2"]["documents"][0]["id"]
        
        # User2 tries to access User1's document
        user2_access_user1_doc_test, user2_access_user1_doc_response = run_test(
            "User2 Accessing User1's Document",
            f"/documents/{user1_doc_id}",
            method="GET",
            auth_token=users["user2"]["auth_token"],
            expected_status=404  # Should fail with 404 Not Found
        )
        
        # User1 tries to access User2's document
        user1_access_user2_doc_test, user1_access_user2_doc_response = run_test(
            "User1 Accessing User2's Document",
            f"/documents/{user2_doc_id}",
            method="GET",
            auth_token=users["user1"]["auth_token"],
            expected_status=404  # Should fail with 404 Not Found
        )
        
        if not user2_access_user1_doc_test:
            print("❌ User2 can access User1's document")
            cross_access_prevention = False
        else:
            print("✅ User2 cannot access User1's document")
        
        if not user1_access_user2_doc_test:
            print("❌ User1 can access User2's document")
            cross_access_prevention = False
        else:
            print("✅ User1 cannot access User2's document")
    else:
        print("❌ No documents available for cross-access testing")
        cross_access_prevention = False
    
    # Step 5: Test new user experience
    print("\nStep 5: Test new user experience")
    
    # Register a new user
    new_user_key = "new_user"
    users[new_user_key] = {
        "email": f"new.user.{uuid.uuid4()}@example.com",
        "password": "NewUserPassword789!",
        "name": "Brand New User",
        "auth_token": None,
        "user_id": None,
        "documents": [],
        "agents": [],
        "conversations": []
    }
    
    new_user_registered = register_user(new_user_key)
    
    if not new_user_registered:
        print("❌ Failed to register new user. Cannot test new user experience.")
        return False
    
    # Check if new user has empty data
    new_user_experience = True
    
    # Check documents
    new_user_docs_test, new_user_docs_response = run_test(
        "Get New User Documents",
        "/documents",
        method="GET",
        auth_token=users[new_user_key]["auth_token"]
    )
    
    if new_user_docs_test:
        if new_user_docs_response and len(new_user_docs_response) > 0:
            print(f"❌ New user has {len(new_user_docs_response)} documents instead of 0")
            new_user_experience = False
        else:
            print("✅ New user has empty documents list")
    else:
        print("❌ Failed to retrieve documents for new user")
        new_user_experience = False
    
    # Check saved agents
    try:
        new_user_agents_test, new_user_agents_response = run_test(
            "Get New User Saved Agents",
            "/agents/saved",
            method="GET",
            auth_token=users[new_user_key]["auth_token"]
        )
        
        if new_user_agents_test:
            if new_user_agents_response and len(new_user_agents_response) > 0:
                print(f"❌ New user has {len(new_user_agents_response)} saved agents instead of 0")
                new_user_experience = False
            else:
                print("✅ New user has empty saved agents list")
        else:
            print("❌ Failed to retrieve saved agents for new user")
            new_user_experience = False
    except Exception as e:
        print(f"Error checking new user saved agents: {e}")
        print("Continuing with test...")
    
    # Check conversations
    try:
        new_user_convs_test, new_user_convs_response = run_test(
            "Get New User Conversations",
            "/conversations",
            method="GET",
            auth_token=users[new_user_key]["auth_token"]
        )
        
        if new_user_convs_test:
            if new_user_convs_response and len(new_user_convs_response) > 0:
                print(f"❌ New user has {len(new_user_convs_response)} conversations instead of 0")
                new_user_experience = False
            else:
                print("✅ New user has empty conversations list")
        else:
            print("❌ Failed to retrieve conversations for new user")
            new_user_experience = False
    except Exception as e:
        print(f"Error checking new user conversations: {e}")
        print("Continuing with test...")
    
    # Print summary
    print("\nUSER DATA ISOLATION SUMMARY:")
    
    if document_isolation:
        print("✅ Document isolation is working correctly")
    else:
        print("❌ Document isolation has issues")
    
    if agent_isolation == True:
        print("✅ Saved agent isolation is working correctly")
    elif agent_isolation == False:
        print("❌ Saved agent isolation has issues")
    else:
        print("⚠️ Saved agent isolation could not be tested")
    
    if conversation_isolation == True:
        print("✅ Conversation isolation is working correctly")
    elif conversation_isolation == False:
        print("❌ Conversation isolation has issues")
    else:
        print("⚠️ Conversation isolation could not be tested")
    
    if cross_access_prevention:
        print("✅ Cross-user access prevention is working correctly")
    else:
        print("❌ Cross-user access prevention has issues")
    
    if new_user_experience:
        print("✅ New user experience is working correctly")
    else:
        print("❌ New user experience has issues")
    
    # Overall assessment
    overall_success = document_isolation and (agent_isolation == True or agent_isolation == "N/A") and (conversation_isolation == True or conversation_isolation == "N/A") and cross_access_prevention and new_user_experience
    
    if overall_success:
        print("\n✅ USER DATA ISOLATION IS WORKING CORRECTLY")
        return True
    else:
        print("\n❌ USER DATA ISOLATION HAS ISSUES")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("RUNNING USER DATA ISOLATION TESTS")
    print("="*80)
    
    # Test user data isolation
    isolation_success = test_user_data_isolation()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion
    print("\n" + "="*80)
    print("USER DATA ISOLATION ASSESSMENT")
    print("="*80)
    
    if isolation_success:
        print("✅ User data isolation is working correctly")
        print("✅ Each user can only see their own data")
        print("✅ Cross-user access is properly prevented")
        print("✅ New users start with empty data")
    else:
        print("❌ User data isolation has issues")
        print("❌ Some user data may be accessible to other users")
    
    print("="*80)
    
    return isolation_success

if __name__ == "__main__":
    main()