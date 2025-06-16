#!/usr/bin/env python3
"""
Test module for enhanced conversation system with strategic question-answer dynamics
"""

import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid
import re

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
created_document_ids = []
test_user_email = f"test.user.{uuid.uuid4()}@example.com"
test_user_password = "securePassword123"
test_user_name = "Test User"

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

def test_login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    # Try using the email/password login first
    login_data = {
        "email": test_user_email,
        "password": test_user_password
    }
    
    login_test, login_response = run_test(
        "Login with credentials",
        "/auth/login",
        method="POST",
        data=login_data,
        expected_keys=["access_token", "token_type", "user"]
    )
    
    # If email/password login fails, try the test login endpoint
    if not login_test or not login_response:
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
    else:
        # Store the token from email/password login
        auth_token = login_response.get("access_token")
        user_data = login_response.get("user", {})
        test_user_id = user_data.get("id")
        print(f"Login successful. User ID: {test_user_id}")
        print(f"JWT Token: {auth_token}")
        return True

def test_strategic_qa_dynamics():
    """Test the enhanced conversation system with strategic question-answer dynamics"""
    print("\n" + "="*80)
    print("TESTING ENHANCED CONVERSATION SYSTEM WITH STRATEGIC Q&A DYNAMICS")
    print("="*80)
    
    # Check if we have auth token
    if not auth_token:
        if not test_login():
            print("❌ Cannot test conversation generation without authentication")
            return False, "Authentication failed"
    
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
    
    # Test 2: Create test agents with diverse expertise areas
    print("\nTest 2: Creating test agents with diverse expertise areas")
    
    # Create agents with different expertise areas
    agent_data = [
        {
            "name": "Dr. Eliza Quantum",
            "archetype": "scientist",
            "personality": {
                "extroversion": 4,
                "optimism": 6,
                "curiosity": 9,
                "cooperativeness": 7,
                "energy": 6
            },
            "goal": "Advance quantum computing research",
            "expertise": "Quantum Physics",
            "background": "Former lead researcher at CERN with focus on quantum entanglement",
            "memory_summary": "",
            "avatar_prompt": "",
            "avatar_url": ""
        },
        {
            "name": "Sarah Mitchell",
            "archetype": "leader",
            "personality": {
                "extroversion": 9,
                "optimism": 8,
                "curiosity": 6,
                "cooperativeness": 8,
                "energy": 8
            },
            "goal": "Deliver successful projects on time and within budget",
            "expertise": "Project Management",
            "background": "20 years experience in tech leadership and complex project delivery",
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
            "background": "Former security consultant specializing in technology risk management",
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
    
    # Test 3: Set a complex scenario that requires diverse expertise
    print("\nTest 3: Setting a complex scenario that requires diverse expertise")
    
    scenario_data = {
        "scenario": "The team is discussing the implementation of a quantum encryption system for a major financial institution. The project has significant technical challenges, tight deadlines, and potential security implications.",
        "scenario_name": "Quantum Encryption Project"
    }
    
    set_scenario_test, set_scenario_response = run_test(
        "Set Complex Scenario",
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
    
    # Generate 5 conversation rounds
    for i in range(5):
        print(f"\nGenerating conversation round {i+1}/5:")
        
        generate_data = {
            "round_number": i+1,
            "time_period": f"Day {i+1} Morning",
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
        else:
            print(f"❌ Failed to generate conversation round {i+1}")
    
    if len(conversation_rounds) < 3:
        print(f"❌ Failed to generate enough conversation rounds. Only generated {len(conversation_rounds)} out of 5.")
        return False, "Failed to generate enough conversation rounds"
    
    # Test 5: Analyze conversation content for strategic questioning
    print("\nTest 5: Analyzing conversation content for strategic questioning")
    
    # Check for strategic questions
    print("\nChecking for strategic questions:")
    strategic_question_count = 0
    total_messages = 0
    
    # Patterns for strategic questions
    strategic_question_patterns = [
        r"based on your (\w+|\s)+ experience",
        r"given your (\w+|\s)+ background",
        r"from your (\w+|\s)+ perspective",
        r"what's your assessment of",
        r"how would you handle",
        r"what risks do you see",
        r"how feasible is",
        r"what would you prioritize",
        r"how would quantum (\w+|\s)+ affect",
        r"what's everyone's take on"
    ]
    
    for round_data in conversation_rounds:
        for message in round_data.get("messages", []):
            total_messages += 1
            message_text = message.get("message", "").lower()
            
            # Check if message contains a question
            if "?" in message_text:
                # Check if it's a strategic question
                for pattern in strategic_question_patterns:
                    if re.search(pattern, message_text):
                        strategic_question_count += 1
                        print(f"Found strategic question: '{message.get('message')}'")
                        break
    
    strategic_question_percentage = (strategic_question_count / total_messages) * 100 if total_messages > 0 else 0
    print(f"Strategic questions: {strategic_question_count}/{total_messages} ({strategic_question_percentage:.1f}%)")
    
    if strategic_question_percentage >= 15:  # Target is 20%, but allow some flexibility
        print("✅ Conversations contain strategic questions (target: ~20%)")
        strategic_questions_ok = True
    else:
        print("❌ Conversations don't contain enough strategic questions")
        strategic_questions_ok = False
    
    # Test 6: Analyze conversation content for question response behavior
    print("\nTest 6: Analyzing conversation content for question response behavior")
    
    # Check for direct answers to questions
    direct_answer_count = 0
    questions_asked = 0
    
    for round_data in conversation_rounds:
        messages = round_data.get("messages", [])
        for i, message in enumerate(messages):
            message_text = message.get("message", "").lower()
            
            # Check if message contains a question
            if "?" in message_text:
                questions_asked += 1
                
                # Check if the next message is a direct answer
                if i < len(messages) - 1:
                    next_message = messages[i + 1]
                    next_message_text = next_message.get("message", "").lower()
                    
                    # Check if next message directly addresses the question
                    if (message.get("agent_name", "") in next_message_text or 
                        any(expertise_word in next_message_text for expertise_word in 
                            next_message.get("agent_expertise", "").lower().split())):
                        direct_answer_count += 1
                        print(f"Found direct answer to question: '{next_message.get('message')}'")
    
    direct_answer_percentage = (direct_answer_count / questions_asked) * 100 if questions_asked > 0 else 0
    print(f"Direct answers to questions: {direct_answer_count}/{questions_asked} ({direct_answer_percentage:.1f}%)")
    
    if direct_answer_percentage >= 70:
        print("✅ Agents provide direct answers to questions")
        direct_answers_ok = True
    else:
        print("❌ Agents don't consistently provide direct answers to questions")
        direct_answers_ok = False
    
    # Test 7: Analyze conversation content for collaborative learning
    print("\nTest 7: Analyzing conversation content for collaborative learning")
    
    # Check for acknowledgment of learning from others
    learning_phrases = [
        "hadn't considered that",
        "good point",
        "that's a valuable insight",
        "i hadn't thought about",
        "that changes my assessment",
        "you've taught me",
        "i've learned",
        "combining your insight with",
        "building on what you said",
        "that's an important perspective"
    ]
    
    learning_count = 0
    
    for round_data in conversation_rounds:
        for message in round_data.get("messages", []):
            message_text = message.get("message", "").lower()
            for phrase in learning_phrases:
                if phrase in message_text:
                    learning_count += 1
                    print(f"Found collaborative learning: '{message.get('message')}'")
                    break
    
    learning_percentage = (learning_count / total_messages) * 100 if total_messages > 0 else 0
    print(f"Collaborative learning instances: {learning_count}/{total_messages} ({learning_percentage:.1f}%)")
    
    if learning_percentage >= 10:
        print("✅ Conversations show collaborative learning")
        collaborative_learning_ok = True
    else:
        print("❌ Conversations don't show enough collaborative learning")
        collaborative_learning_ok = False
    
    # Test 8: Analyze conversation content for interactive conversation flow
    print("\nTest 8: Analyzing conversation content for interactive conversation flow")
    
    # Check for natural question-answer exchanges
    qa_exchanges = 0
    
    for round_data in conversation_rounds:
        messages = round_data.get("messages", [])
        for i in range(len(messages) - 1):
            current_message = messages[i]
            next_message = messages[i + 1]
            
            current_text = current_message.get("message", "").lower()
            next_text = next_message.get("message", "").lower()
            
            # Check if current message has a question and next message is an answer
            if "?" in current_text and (
                current_message.get("agent_name", "") in next_text or
                any(expertise_word in next_text for expertise_word in 
                    next_message.get("agent_expertise", "").lower().split())):
                qa_exchanges += 1
                print(f"Found Q&A exchange: Q: '{current_message.get('message')}' A: '{next_message.get('message')}'")
    
    qa_exchange_percentage = (qa_exchanges / (total_messages / 2)) * 100 if total_messages > 0 else 0
    print(f"Question-answer exchanges: {qa_exchanges} ({qa_exchange_percentage:.1f}% of potential exchanges)")
    
    if qa_exchanges >= 3:  # At least 3 clear Q&A exchanges
        print("✅ Conversations show natural question-answer exchanges")
        qa_exchanges_ok = True
    else:
        print("❌ Conversations don't show enough natural question-answer exchanges")
        qa_exchanges_ok = False
    
    # Print summary
    print("\nENHANCED CONVERSATION SYSTEM WITH STRATEGIC Q&A DYNAMICS SUMMARY:")
    
    # Check if all tests passed
    has_strategic_questions = strategic_questions_ok
    has_direct_answers = direct_answers_ok
    has_collaborative_learning = collaborative_learning_ok
    has_qa_exchanges = qa_exchanges_ok
    
    if has_strategic_questions and has_direct_answers and has_collaborative_learning and has_qa_exchanges:
        print("✅ Enhanced conversation system with strategic Q&A dynamics is working correctly!")
        print(f"✅ Strategic questions: {strategic_question_percentage:.1f}% of messages (target: ~20%)")
        print(f"✅ Direct answers to questions: {direct_answer_percentage:.1f}% of questions")
        print(f"✅ Collaborative learning instances: {learning_percentage:.1f}% of messages")
        print(f"✅ Question-answer exchanges: {qa_exchanges} natural exchanges")
        return True, "Enhanced conversation system with strategic Q&A dynamics is working correctly"
    else:
        issues = []
        if not has_strategic_questions:
            issues.append(f"Only {strategic_question_percentage:.1f}% of messages contain strategic questions (target: ~20%)")
        if not has_direct_answers:
            issues.append(f"Only {direct_answer_percentage:.1f}% of questions receive direct answers")
        if not has_collaborative_learning:
            issues.append(f"Only {learning_percentage:.1f}% of messages show collaborative learning")
        if not has_qa_exchanges:
            issues.append(f"Only {qa_exchanges} natural question-answer exchanges found")
        
        print("❌ Enhanced conversation system with strategic Q&A dynamics has issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False, {"issues": issues}

if __name__ == "__main__":
    # Test login first to get auth token
    test_login()
    
    # Test strategic Q&A dynamics
    test_strategic_qa_dynamics()
    
    # Print summary
    print_summary()