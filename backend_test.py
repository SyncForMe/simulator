#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import base64
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

def main():
    """Run API tests for avatar generation functionality"""
    print("Starting API tests for avatar generation functionality...")
    
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
    
    # 2. Test avatar generation functionality
    avatar_success, avatar_message = test_avatar_generation()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion about the avatar generation
    print("\n" + "="*80)
    print("AVATAR GENERATION FUNCTIONALITY ASSESSMENT")
    print("="*80)
    if avatar_success:
        print("✅ The avatar generation functionality is working correctly!")
        print("✅ The /api/avatars/generate endpoint is successfully generating avatar images.")
        print("✅ Agent creation with avatar generation is working properly.")
        print("✅ Error handling for avatar generation is implemented correctly.")
    else:
        print("❌ The avatar generation functionality is NOT working correctly.")
        print("❌ One or more avatar-related endpoints are returning errors.")
        print("\nPossible issues:")
        print("1. The /api/avatars/generate endpoint might not be implemented")
        print("2. The fal.ai integration might not be configured correctly")
        print("3. The API key for fal.ai might be invalid or have insufficient permissions")
    print("="*80)

if __name__ == "__main__":
    main()
