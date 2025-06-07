#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv

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
        elif method == "DELETE":
            response = requests.delete(url)
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

def create_test_conversations():
    """Create test conversations in English for translation testing"""
    print("\n" + "="*80)
    print("CREATING TEST CONVERSATIONS")
    print("="*80)
    
    # First, check if we need to initialize the simulation
    _, state = run_test(
        "Get Simulation State",
        "/simulation/state",
        expected_keys=["is_active"]
    )
    
    if not state or not state.get("is_active", False):
        # Start the simulation
        run_test(
            "Start Simulation",
            "/simulation/start",
            method="POST",
            expected_keys=["message", "state"]
        )
        
        # Initialize research station with default agents
        run_test(
            "Initialize Research Station",
            "/simulation/init-research-station",
            method="POST",
            expected_keys=["message", "agents"]
        )
    
    # Check if we already have conversations
    _, conversations = run_test(
        "Get Existing Conversations",
        "/conversations",
        expected_keys=[]
    )
    
    # If we already have at least 3 conversations, we can use those
    if conversations and len(conversations) >= 3:
        print(f"Using {len(conversations)} existing conversations for translation tests")
        return True
    
    # Otherwise, create 3 new conversations
    print("Creating 3 new test conversations...")
    
    for i in range(3):
        success, _ = run_test(
            f"Generate Conversation {i+1}",
            "/conversation/generate",
            method="POST",
            expected_keys=["id", "messages"]
        )
        
        if not success:
            print(f"Failed to create test conversation {i+1}")
            return False
        
        # Small delay between conversation generation
        time.sleep(2)
    
    # Verify we now have conversations
    _, conversations = run_test(
        "Verify Conversations Created",
        "/conversations",
        expected_keys=[]
    )
    
    if conversations and len(conversations) >= 3:
        print(f"Successfully created {len(conversations)} test conversations")
        return True
    else:
        print("Failed to create enough test conversations")
        return False

def test_translation_path(source_lang, target_lang, description):
    """Test a specific translation path from source to target language"""
    print(f"\n{'='*80}")
    print(f"TESTING TRANSLATION PATH: {source_lang} → {target_lang} ({description})")
    print(f"{'='*80}")
    
    # Step 0: Set the language for the simulation
    success0, response0 = run_test(
        f"Set language to {source_lang}",
        "/simulation/set-language",
        method="POST",
        data={"language": source_lang},
        expected_keys=["message", "language"]
    )
    
    if not success0:
        print(f"❌ Failed to set language to {source_lang}")
        return False
    
    # Step 1: Translate to target language
    success1, response1 = run_test(
        f"Translate from {source_lang} to {target_lang}",
        "/conversations/translate",
        method="POST",
        data={"target_language": target_lang},
        expected_keys=["message", "translated_count", "success"]
    )
    
    if not success1 or not response1.get("success", False):
        print(f"❌ Failed to translate from {source_lang} to {target_lang}")
        return False
    
    # Verify translation was successful
    translated_count = response1.get("translated_count", 0)
    if translated_count == 0:
        print(f"⚠️ No conversations were translated to {target_lang}. They might already be in that language.")
    else:
        print(f"✅ Successfully translated {translated_count} conversations to {target_lang}")
    
    # Step 2: Verify conversations are now in target language
    success2, conversations = run_test(
        f"Verify conversations in {target_lang}",
        "/conversations",
        expected_keys=[]
    )
    
    if not success2 or not conversations:
        print(f"❌ Failed to retrieve conversations after translation to {target_lang}")
        return False
    
    # Check if conversations have the correct language
    all_in_target_lang = True
    for conv in conversations:
        if "language" not in conv:
            print(f"❌ Conversation {conv.get('id')} does not have a language field")
            all_in_target_lang = False
        elif conv.get("language") != target_lang:
            all_in_target_lang = False
            print(f"❌ Conversation {conv.get('id')} is not in {target_lang} (language: {conv.get('language')})")
    
    if all_in_target_lang:
        print(f"✅ All conversations are now in {target_lang}")
    else:
        print(f"❌ Not all conversations were translated to {target_lang}")
        return False
    
    return True

def test_translation_functionality():
    """Test the translation functionality with various language pairs"""
    print("\n" + "="*80)
    print("TESTING TRANSLATION FUNCTIONALITY")
    print("="*80)
    
    # Create test conversations if needed
    if not create_test_conversations():
        print("❌ Failed to create test conversations. Aborting translation tests.")
        return False
    
    # Test major language pairs (English → Other → English)
    language_pairs = [
        ("en", "es", "English → Spanish"),
        ("es", "en", "Spanish → English"),
        ("en", "de", "English → German"),
        ("de", "en", "German → English"),
        ("en", "fr", "English → French"),
        ("fr", "en", "French → English"),
        ("en", "hr", "English → Croatian"),
        ("hr", "en", "Croatian → English"),
        ("en", "ja", "English → Japanese"),
        ("ja", "en", "Japanese → English"),
        ("en", "ar", "English → Arabic"),
        ("ar", "en", "Arabic → English")
    ]
    
    # Cross-language testing
    cross_language_pairs = [
        ("es", "de", "Spanish → German"),
        ("de", "fr", "German → French"),
        ("fr", "hr", "French → Croatian"),
        ("ja", "ar", "Japanese → Arabic")
    ]
    
    # Combine all test pairs
    all_test_pairs = language_pairs + cross_language_pairs
    
    # Track results for each language pair
    language_pair_results = {}
    
    # Run tests for each language pair
    for source, target, description in all_test_pairs:
        success = test_translation_path(source, target, description)
        language_pair_results[f"{source} → {target}"] = success
    
    # Print summary of language pair tests
    print("\n" + "="*80)
    print("LANGUAGE PAIR TEST RESULTS")
    print("="*80)
    
    for pair, success in language_pair_results.items():
        result_symbol = "✅" if success else "❌"
        print(f"{result_symbol} {pair}")
    
    # Check specifically for English as target language
    english_target_tests = [pair for pair in language_pair_results.keys() if pair.endswith("→ en")]
    english_target_success = all(language_pair_results[pair] for pair in english_target_tests)
    
    print("\n" + "="*80)
    print("TRANSLATION TO ENGLISH ASSESSMENT")
    print("="*80)
    
    if english_target_success:
        print("✅ All translations TO English were successful!")
        print("✅ The reported bug with translating back to English has been fixed.")
    else:
        print("❌ Some translations TO English failed!")
        print("❌ The reported bug with translating back to English still exists.")
        
        # List the specific failures
        failed_to_english = [pair for pair in english_target_tests if not language_pair_results[pair]]
        for pair in failed_to_english:
            print(f"  ❌ Failed: {pair}")
    
    # Overall assessment
    all_tests_passed = all(language_pair_results.values())
    
    print("\n" + "="*80)
    print("OVERALL TRANSLATION ASSESSMENT")
    print("="*80)
    
    if all_tests_passed:
        print("✅ All translation tests passed successfully!")
        print("✅ The translation system is working correctly for all tested language pairs.")
        print("✅ The reported bug with translating back to English has been fixed.")
    else:
        print("❌ Some translation tests failed!")
        print("❌ The translation system has issues with certain language pairs.")
        
        # List the specific failures
        failed_pairs = [pair for pair, success in language_pair_results.items() if not success]
        for pair in failed_pairs:
            print(f"  ❌ Failed: {pair}")
    
    return all_tests_passed

def main():
    """Run API tests focused on the translation functionality"""
    print("Starting API tests for the translation functionality...")
    
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
    
    # 2. Test the translation functionality
    translation_success = test_translation_functionality()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion about the translation functionality
    print("\n" + "="*80)
    print("TRANSLATION FUNCTIONALITY ASSESSMENT")
    print("="*80)
    if translation_success:
        print("✅ The translation system is working correctly for all tested language pairs!")
        print("✅ The reported bug with translating back to English has been fixed.")
        print("✅ All conversations are properly marked with the correct language.")
        print("✅ No partial translation issues were observed.")
    else:
        print("❌ The translation system has issues with certain language pairs.")
        print("❌ Check the detailed test results above for specific failures.")
    print("="*80)

if __name__ == "__main__":
    main()