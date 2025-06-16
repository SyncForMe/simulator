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

def register_user(email, password, name):
    """Register a new user and return the auth token"""
    register_data = {
        "email": email,
        "password": password,
        "name": name
    }
    
    print(f"Registering user: {name} ({email})")
    
    response = requests.post(f"{API_URL}/auth/register", json=register_data)
    
    if response.status_code == 200:
        response_data = response.json()
        auth_token = response_data.get("access_token")
        user_data = response_data.get("user", {})
        user_id = user_data.get("id")
        print(f"User registered with ID: {user_id}")
        return auth_token, user_id
    else:
        print(f"Registration failed: {response.status_code} - {response.text}")
        return None, None

def get_conversations(auth_token):
    """Get conversations for a user"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.get(f"{API_URL}/conversations", headers=headers)
    
    if response.status_code == 200:
        conversations = response.json()
        print(f"Found {len(conversations)} conversations")
        return conversations
    else:
        print(f"Failed to get conversations: {response.status_code} - {response.text}")
        return []

def get_conversation_history(auth_token):
    """Get conversation history for a user"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.get(f"{API_URL}/conversation-history", headers=headers)
    
    if response.status_code == 200:
        history = response.json()
        print(f"Found {len(history)} conversation history items")
        return history
    else:
        print(f"Failed to get conversation history: {response.status_code} - {response.text}")
        return []

def get_agents(auth_token):
    """Get agents for a user"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.get(f"{API_URL}/agents", headers=headers)
    
    if response.status_code == 200:
        agents = response.json()
        print(f"Found {len(agents)} agents")
        return agents
    else:
        print(f"Failed to get agents: {response.status_code} - {response.text}")
        return []

def get_saved_agents(auth_token):
    """Get saved agents for a user"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    response = requests.get(f"{API_URL}/saved-agents", headers=headers)
    
    if response.status_code == 200:
        saved_agents = response.json()
        print(f"Found {len(saved_agents)} saved agents")
        return saved_agents
    else:
        print(f"Failed to get saved agents: {response.status_code} - {response.text}")
        return []

def main():
    """Test if a new user can see conversations from other users"""
    print("\n" + "="*80)
    print("TESTING USER DATA ISOLATION FOR CONVERSATIONS")
    print("="*80)
    
    # Create 5 new users
    users = []
    for i in range(5):
        email = f"test.user.{uuid.uuid4()}@example.com"
        password = "securePassword123"
        name = f"Test User {i+1}"
        
        auth_token, user_id = register_user(email, password, name)
        
        if auth_token:
            users.append({
                "email": email,
                "name": name,
                "auth_token": auth_token,
                "user_id": user_id
            })
    
    print(f"\nCreated {len(users)} test users")
    
    # Check conversations for each user
    for i, user in enumerate(users):
        print(f"\nChecking data for {user['name']} ({user['email']})")
        
        # Check conversations
        conversations = get_conversations(user["auth_token"])
        
        # Check conversation history
        history = get_conversation_history(user["auth_token"])
        
        # Check agents
        agents = get_agents(user["auth_token"])
        
        # Check saved agents
        saved_agents = get_saved_agents(user["auth_token"])
        
        # Print summary for this user
        print(f"\nSummary for {user['name']}:")
        print(f"- Conversations: {len(conversations)}")
        print(f"- Conversation History: {len(history)}")
        print(f"- Agents: {len(agents)}")
        print(f"- Saved Agents: {len(saved_agents)}")
    
    # Print overall summary
    print("\n" + "="*80)
    print("USER DATA ISOLATION SUMMARY")
    print("="*80)
    
    # Check if any user has conversations
    has_conversations = any(len(get_conversations(user["auth_token"])) > 0 for user in users)
    has_history = any(len(get_conversation_history(user["auth_token"])) > 0 for user in users)
    
    if has_conversations:
        print("❌ Some users can see conversations - DATA ISOLATION FAILURE")
    else:
        print("✅ No users can see conversations - DATA ISOLATION WORKING")
    
    if has_history:
        print("❌ Some users can see conversation history - DATA ISOLATION FAILURE")
    else:
        print("✅ No users can see conversation history - DATA ISOLATION WORKING")
    
    # Check if all users see the same number of agents
    agent_counts = [len(get_agents(user["auth_token"])) for user in users]
    if len(set(agent_counts)) == 1:
        print(f"✅ All users see the same number of agents ({agent_counts[0]}) - CONSISTENT")
    else:
        print(f"❌ Users see different numbers of agents {agent_counts} - INCONSISTENT")
    
    # Check if all users have empty saved agents
    saved_agent_counts = [len(get_saved_agents(user["auth_token"])) for user in users]
    if all(count == 0 for count in saved_agent_counts):
        print("✅ All users have empty saved agents - DATA ISOLATION WORKING")
    else:
        print("❌ Some users can see saved agents - DATA ISOLATION FAILURE")
    
    print("="*80)

if __name__ == "__main__":
    main()