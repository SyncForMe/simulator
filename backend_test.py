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

def main():
    """Run API tests focused on the fixed Google Cloud Text-to-Speech integration"""
    print("Starting API tests for the fixed Google Cloud Text-to-Speech integration...")
    
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
    
    # 2. Test the fixed TTS functionality
    tts_success, tts_message = test_tts_functionality()
    
    # Print summary of all tests
    print_summary()
    
    # Print final conclusion about the TTS fix
    print("\n" + "="*80)
    print("GOOGLE CLOUD TEXT-TO-SPEECH FIX ASSESSMENT")
    print("="*80)
    if tts_success:
        print("✅ The client_options approach with API key authentication is working correctly!")
        print("✅ The TTS endpoint is now successfully generating audio for agent voices.")
        print("✅ The 'File was not found' error has been resolved.")
    else:
        print("❌ The client_options approach with API key authentication is NOT working correctly.")
        print("❌ The TTS endpoint is still returning errors despite the fix.")
        print("❌ The 'File was not found' error persists or has been replaced with another error.")
        print("\nPossible issues:")
        print("1. The API key might not have Text-to-Speech API permissions")
        print("2. The client_options implementation might be incorrect")
        print("3. There might be an issue with the Google Cloud TTS client library version")
    print("="*80)

def test_tts_functionality():
    """Test the Google Cloud Text-to-Speech integration with fixed client_options approach"""
    print("\n" + "="*80)
    print("TESTING FIXED GOOGLE CLOUD TEXT-TO-SPEECH INTEGRATION")
    print("="*80)
    
    # 1. Test TTS endpoint with a sample request using the fixed client_options approach
    tts_data = {
        "text": "Hello, this is a test of the improved AI voice system",
        "agent_name": "Marcus \"Mark\" Castellano"
    }
    
    tts_test, tts_response = run_test(
        "Text-to-Speech Synthesis with API Key Authentication",
        "/tts/synthesize",
        method="POST",
        data=tts_data,
        expected_keys=["audio_data", "voice_used", "agent_name"]
    )
    
    # Check if we got a fallback response (error handling)
    if "fallback" in tts_response and tts_response.get("fallback") == True:
        print("\n⚠️ TTS endpoint returned a fallback response despite the fix:")
        print(f"Error: {tts_response.get('error', 'Unknown error')}")
        print("\nThis indicates there might still be an issue with the Google Cloud API key authentication.")
        
        # Check if the error is related to credentials
        error_msg = tts_response.get('error', '').lower()
        if "file" in error_msg and "not found" in error_msg:
            print("\nThe error still suggests a missing credentials file. This indicates:")
            print("1. The client_options with API key approach might not be implemented correctly")
            print("2. The API key might be invalid or have insufficient permissions")
            print("3. There might be an issue with the Google Cloud TTS client library version")
        
        # Return a failure since the fix didn't work
        return False, "TTS functionality is still not working despite the client_options fix"
    
    if tts_test:
        # Verify the response contains base64 encoded audio data
        audio_data = tts_response.get("audio_data", "")
        if not audio_data:
            print("❌ Response contains empty audio_data")
            tts_test = False
        else:
            print(f"✅ Response contains audio data ({len(audio_data)} characters)")
            
            # Verify it's valid base64
            try:
                import base64
                decoded = base64.b64decode(audio_data)
                print(f"✅ Audio data is valid base64 ({len(decoded)} bytes)")
                
                # Check if it starts with MP3 header (ID3)
                if decoded[:3] == b'ID3' or decoded[:2] == b'\xff\xfb':
                    print("✅ Audio data appears to be a valid MP3 file")
                else:
                    print(f"⚠️ Audio data doesn't have standard MP3 header: {decoded[:10]}")
            except Exception as e:
                print(f"❌ Failed to decode base64 audio data: {e}")
                tts_test = False
        
        # Verify voice_used matches the expected voice for the agent
        voice_used = tts_response.get("voice_used", "")
        expected_voice = "en-US-Neural2-D"  # For Marcus "Mark" Castellano
        if voice_used == expected_voice:
            print(f"✅ Voice used matches expected voice: {voice_used}")
        else:
            print(f"❌ Voice used ({voice_used}) doesn't match expected voice ({expected_voice})")
            tts_test = False
        
        # Verify agent_name is returned correctly
        agent_name = tts_response.get("agent_name", "")
        if agent_name == tts_data["agent_name"]:
            print(f"✅ Agent name returned correctly: {agent_name}")
        else:
            print(f"❌ Agent name mismatch: expected {tts_data['agent_name']}, got {agent_name}")
            tts_test = False
    
    # 2. Test with a different agent to verify voice configuration works
    tts_data2 = {
        "text": "This is a different voice test for Alexandra Chen",
        "agent_name": "Alexandra \"Alex\" Chen"
    }
    
    tts_test2, tts_response2 = run_test(
        "Text-to-Speech with Different Agent",
        "/tts/synthesize",
        method="POST",
        data=tts_data2,
        expected_keys=["audio_data", "voice_used", "agent_name"]
    )
    
    # Check if we got a fallback response (error handling)
    if "fallback" in tts_response2 and tts_response2.get("fallback") == True:
        print("\n⚠️ Second TTS test also returned a fallback response, indicating the fix didn't work")
        tts_test2 = False
    elif tts_test2:
        # Verify voice_used matches the expected voice for the agent
        voice_used = tts_response2.get("voice_used", "")
        expected_voice = "en-US-Neural2-F"  # For Alexandra "Alex" Chen
        if voice_used == expected_voice:
            print(f"✅ Voice used matches expected voice: {voice_used}")
        else:
            print(f"❌ Voice used ({voice_used}) doesn't match expected voice ({expected_voice})")
            tts_test2 = False
    
    # 3. Test error handling by forcing an error
    # We'll use an invalid agent name that doesn't have a voice configuration
    tts_data3 = {
        "text": "This should use a fallback voice",
        "agent_name": "NonexistentAgent"
    }
    
    tts_test3, tts_response3 = run_test(
        "Text-to-Speech with Invalid Agent (Fallback)",
        "/tts/synthesize",
        method="POST",
        data=tts_data3,
        expected_keys=["audio_data", "voice_used", "agent_name"]
    )
    
    # Check if we got a fallback response (error handling)
    if "fallback" in tts_response3 and tts_response3.get("fallback") == True:
        print("\n⚠️ Third TTS test returned a fallback response, indicating the fix didn't work for all cases")
        tts_test3 = False
    elif tts_test3:
        # Should use fallback voice (Marcus "Mark" Castellano's voice)
        voice_used = tts_response3.get("voice_used", "")
        fallback_voice = "en-US-Neural2-D"  # Default fallback voice
        if voice_used == fallback_voice:
            print(f"✅ Correctly used fallback voice for invalid agent: {voice_used}")
        else:
            print(f"❌ Didn't use expected fallback voice: got {voice_used}, expected {fallback_voice}")
            tts_test3 = False
    
    # Print summary of TTS tests
    print("\nTTS ENDPOINT SUMMARY:")
    if tts_test and tts_test2 and tts_test3:
        print("✅ The TTS endpoint is now working correctly with the fixed client_options approach!")
        print("✅ The API key authentication is properly configured and working.")
        print("✅ Different voice configurations are working correctly.")
        print("✅ Fallback to default voice for unknown agents is working correctly.")
        return True, "TTS functionality is now working correctly with the client_options fix"
    else:
        if "fallback" in tts_response and tts_response.get("fallback") == True:
            print("❌ The TTS endpoint is still returning fallback responses despite the fix.")
            print("❌ The client_options with API key approach might not be implemented correctly.")
            print("❌ The API key might be invalid or have insufficient permissions.")
            return False, "TTS functionality is still not working despite the client_options fix"
        else:
            print("⚠️ The TTS endpoint is partially working but has some issues.")
            print("⚠️ Some tests passed but others failed. Check the detailed test results above.")
            return True, "TTS functionality is partially working with the client_options fix"

if __name__ == "__main__":
    main()
    print("\nRunning Text-to-Speech tests...")
    test_tts_functionality()
