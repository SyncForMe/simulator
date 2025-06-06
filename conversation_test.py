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

def run_test(test_name, endpoint, method="GET", data=None):
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
            return None
        
        # Print response details
        print(f"Status Code: {response.status_code}")
        
        # Check if response is JSON
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            return response_data
        except json.JSONDecodeError:
            print(f"Response is not JSON: {response.text}")
            return None
    
    except Exception as e:
        print(f"Error during test: {e}")
        return None

def main():
    """Investigate conversation generation and auto-mode issues"""
    print("Starting investigation of conversation generation and auto-mode issues...")
    
    # 1. Check current simulation state
    print("\nChecking current simulation state...")
    state_data = run_test("Get Simulation State", "/simulation/state")
    
    if state_data:
        print("\nCurrent simulation state:")
        print(f"  - Day: {state_data.get('current_day')}")
        print(f"  - Time Period: {state_data.get('current_time_period')}")
        print(f"  - Active: {state_data.get('is_active')}")
        print(f"  - Auto Conversations: {state_data.get('auto_conversations', False)}")
        print(f"  - Auto Time: {state_data.get('auto_time', False)}")
        print(f"  - Conversation Interval: {state_data.get('conversation_interval')}")
        print(f"  - Time Interval: {state_data.get('time_interval')}")
    
    # 2. Check API usage
    print("\nChecking API usage...")
    api_usage_data = run_test("Get API Usage", "/api-usage")
    
    if api_usage_data:
        print("\nAPI Usage Status:")
        print(f"  - Requests Used: {api_usage_data.get('requests_used')}/{api_usage_data.get('max_requests')}")
        print(f"  - Remaining: {api_usage_data.get('remaining')}")
        print(f"  - API Available: {api_usage_data.get('api_available')}")
        if api_usage_data.get('note'):
            print(f"  - Note: {api_usage_data.get('note')}")
    
    # 3. Test manual conversation generation
    print("\nTesting manual conversation generation...")
    conv_data = run_test("Generate Conversation", "/conversation/generate", method="POST")
    
    if conv_data:
        messages = conv_data.get("messages", [])
        if len(messages) < 1:
            print("No messages generated in the conversation")
        else:
            print("\nVerifying conversation quality:")
            
            # Check for generic fallback patterns
            generic_patterns = [
                "is analyzing",
                "is questioning",
                "is taking a moment",
                "is carefully considering",
                "nods thoughtfully",
                "API limit reached"
            ]
            
            all_valid = True
            for i, msg in enumerate(messages):
                agent_name = msg.get("agent_name", "Unknown")
                message_text = msg.get("message", "")
                
                # Check if message is a generic fallback
                is_generic = False
                for pattern in generic_patterns:
                    if pattern in message_text:
                        is_generic = True
                        break
                
                # Check if message is too short
                is_too_short = len(message_text) < 10
                
                if is_generic or is_too_short:
                    print(f"  ❌ {agent_name}: '{message_text}' (Generic fallback or too short)")
                    all_valid = False
                else:
                    print(f"  ✅ {agent_name}: '{message_text}'")
            
            if all_valid:
                print("\nSuccess: All agent responses are actual dialogue, not generic fallbacks")
            else:
                print("\nWarning: Some agent responses are generic fallbacks, which may indicate API quota issues")
    
    # 4. Test observer input
    print("\nTesting observer input functionality...")
    observer_data = {
        "observer_message": "What progress have you made on the project so far?"
    }
    observer_result = run_test("Send Observer Message", "/observer/send-message", method="POST", data=observer_data)
    
    if observer_result:
        agent_responses = observer_result.get("agent_responses", {}).get("messages", [])
        if len(agent_responses) < 1:
            print("No agent responses to observer message")
        else:
            print("\nVerifying agent responses to observer:")
            
            # Check for generic fallback patterns
            generic_patterns = [
                "is analyzing",
                "is questioning",
                "is taking a moment",
                "is carefully considering",
                "nods thoughtfully",
                "API limit reached"
            ]
            
            all_valid = True
            for i, msg in enumerate(agent_responses):
                agent_name = msg.get("agent_name", "Unknown")
                message_text = msg.get("message", "")
                
                # Check if message is a generic fallback
                is_generic = False
                for pattern in generic_patterns:
                    if pattern in message_text:
                        is_generic = True
                        break
                
                # Check if message is too short
                is_too_short = len(message_text) < 10
                
                if is_generic or is_too_short:
                    print(f"  ❌ {agent_name}: '{message_text}' (Generic fallback or too short)")
                    all_valid = False
                else:
                    print(f"  ✅ {agent_name}: '{message_text}'")
            
            if all_valid:
                print("\nSuccess: All agent responses to observer are actual dialogue, not generic fallbacks")
            else:
                print("\nWarning: Some agent responses to observer are generic fallbacks, which may indicate API quota issues")
    
    # 5. Toggle auto-mode on
    print("\nTesting auto-mode toggle functionality...")
    auto_mode_data = {
        "auto_conversations": True,
        "auto_time": True,
        "conversation_interval": 15,
        "time_interval": 45
    }
    auto_result = run_test("Toggle Auto Mode On", "/simulation/toggle-auto-mode", method="POST", data=auto_mode_data)
    
    if auto_result:
        print("\nAuto mode settings:")
        print(f"  - Auto Conversations: {auto_result.get('auto_conversations')}")
        print(f"  - Auto Time: {auto_result.get('auto_time')}")
        print(f"  - Conversation Interval: {auto_result.get('conversation_interval')} seconds")
        print(f"  - Time Interval: {auto_result.get('time_interval')} seconds")
        
        # Verify settings were saved in simulation state
        state_after_data = run_test("Verify Auto Mode Settings", "/simulation/state")
        
        if state_after_data:
            auto_conversations = state_after_data.get('auto_conversations')
            auto_time = state_after_data.get('auto_time')
            conversation_interval = state_after_data.get('conversation_interval')
            time_interval = state_after_data.get('time_interval')
            
            print("\nAuto mode settings in simulation state:")
            print(f"  - Auto Conversations: {auto_conversations}")
            print(f"  - Auto Time: {auto_time}")
            print(f"  - Conversation Interval: {conversation_interval}")
            print(f"  - Time Interval: {time_interval}")
            
            # Verify settings match what we sent
            settings_match = (
                auto_conversations == auto_mode_data["auto_conversations"] and
                auto_time == auto_mode_data["auto_time"] and
                conversation_interval == auto_mode_data["conversation_interval"] and
                time_interval == auto_mode_data["time_interval"]
            )
            
            if settings_match:
                print("✅ Auto mode settings correctly saved in simulation state")
            else:
                print("❌ Auto mode settings in simulation state don't match requested values")
    
    # 6. Get recent conversations to check history
    print("\nChecking recent conversation history...")
    conversations_data = run_test("Get Conversations", "/conversations")
    
    if conversations_data and isinstance(conversations_data, list):
        print(f"\nFound {len(conversations_data)} conversations in history")
        
        if len(conversations_data) > 0:
            # Analyze the last few conversations to see if they show a pattern
            recent_convs = conversations_data[-5:] if len(conversations_data) >= 5 else conversations_data
            
            print("\nAnalyzing recent conversations for patterns:")
            for i, conv in enumerate(recent_convs):
                day_period = conv.get("time_period", "Unknown")
                messages = conv.get("messages", [])
                
                print(f"\nConversation {len(conversations_data)-len(recent_convs)+i+1}/{len(conversations_data)} - {day_period}:")
                
                # Check for generic fallback patterns
                generic_count = 0
                for msg in messages:
                    agent_name = msg.get("agent_name", "Unknown")
                    message_text = msg.get("message", "")
                    
                    # Check if message is a generic fallback
                    is_generic = False
                    for pattern in ["is analyzing", "is questioning", "is taking a moment", "is carefully considering", "nods thoughtfully", "API limit reached"]:
                        if pattern in message_text:
                            is_generic = True
                            break
                    
                    if is_generic or len(message_text) < 10:
                        generic_count += 1
                        print(f"  ❌ {agent_name}: '{message_text}' (Generic)")
                    else:
                        print(f"  ✅ {agent_name}: '{message_text[:50]}...' (Authentic)")
                
                generic_percentage = (generic_count / len(messages)) * 100 if messages else 0
                print(f"  Generic responses: {generic_count}/{len(messages)} ({generic_percentage:.1f}%)")
    
    # 7. Toggle auto-mode off
    print("\nTurning auto-mode off...")
    auto_mode_off_data = {
        "auto_conversations": False,
        "auto_time": False,
        "conversation_interval": 10,
        "time_interval": 30
    }
    auto_off_result = run_test("Toggle Auto Mode Off", "/simulation/toggle-auto-mode", method="POST", data=auto_mode_off_data)
    
    # Provide analysis of the issue
    print("\n" + "="*80)
    print("ISSUE ANALYSIS")
    print("="*80)
    
    if api_usage_data:
        if api_usage_data.get('api_available') == "quota_exceeded":
            print("CRITICAL ISSUE: API quota has been exceeded. This is preventing the generation of authentic conversations.")
            print("The system is falling back to generic responses when API limits are reached.")
            print("Recommendation: Wait for the API quota to reset (typically daily) or upgrade the API plan.")
        elif api_usage_data.get('requests_used', 0) > 900:
            print("WARNING: API usage is approaching the limit (>900 requests). This may cause intermittent failures.")
            print("The system may start falling back to generic responses as the limit is approached.")
            print("Recommendation: Monitor API usage and consider reducing usage or upgrading the API plan.")
    
    if state_data and not state_data.get('auto_conversations', False):
        print("ISSUE: Auto-conversations mode is currently disabled. This explains why conversations aren't generating automatically.")
        print("Recommendation: Enable auto-conversations mode using the toggle-auto-mode endpoint.")
    
    if conv_data and any("API limit reached" in msg.get("message", "") for msg in conv_data.get("messages", [])):
        print("ISSUE: Some conversation messages indicate API limits have been reached.")
        print("This is causing the system to use fallback responses instead of generating authentic dialogue.")
        print("Recommendation: Wait for API quota to reset or upgrade the API plan.")
    
    print("\nSUMMARY OF FINDINGS:")
    if api_usage_data:
        print(f"- API Usage: {api_usage_data.get('requests_used')}/{api_usage_data.get('max_requests')} requests used")
        print(f"- API Status: {'Available' if api_usage_data.get('api_available') == True else 'Unavailable or Limited'}")
    
    if state_data:
        print(f"- Auto Conversations: {'Enabled' if state_data.get('auto_conversations', False) else 'Disabled'}")
        print(f"- Auto Time Progression: {'Enabled' if state_data.get('auto_time', False) else 'Disabled'}")
    
    if conversations_data and isinstance(conversations_data, list) and len(conversations_data) > 0:
        recent_convs = conversations_data[-5:] if len(conversations_data) >= 5 else conversations_data
        generic_msgs = sum(1 for conv in recent_convs for msg in conv.get("messages", []) 
                         if any(pattern in msg.get("message", "") 
                               for pattern in ["is analyzing", "is questioning", "is taking a moment", 
                                              "is carefully considering", "nods thoughtfully", "API limit reached"]))
        total_msgs = sum(len(conv.get("messages", [])) for conv in recent_convs)
        generic_percentage = (generic_msgs / total_msgs) * 100 if total_msgs else 0
        
        print(f"- Recent Conversations Quality: {generic_percentage:.1f}% generic responses")

if __name__ == "__main__":
    main()