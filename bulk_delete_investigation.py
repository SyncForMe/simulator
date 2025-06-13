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

# Global variables for auth testing
auth_token = None
test_user_id = None

def print_separator(title):
    """Print a separator with a title"""
    print("\n" + "="*80)
    print(title)
    print("="*80)

def login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    print_separator("LOGGING IN")
    url = f"{API_URL}/auth/test-login"
    
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            auth_token = data.get("access_token")
            user_data = data.get("user", {})
            test_user_id = user_data.get("id")
            
            print(f"Login successful. User ID: {test_user_id}")
            print(f"JWT Token: {auth_token}")
            return True
        else:
            print(f"Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"Error during login: {e}")
        return False

def get_conversations():
    """Get all conversations for the authenticated user"""
    print_separator("GETTING CONVERSATIONS")
    url = f"{API_URL}/conversation-history"
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} conversations")
            
            # Print details of first 3 conversations
            for i, conv in enumerate(data[:3]):
                print(f"\nConversation {i+1}:")
                print(f"  ID: {conv.get('id')}")
                print(f"  Title: {conv.get('title')}")
                print(f"  Created: {conv.get('created_at')}")
                print(f"  Participants: {', '.join(conv.get('participants', []))}")
                
            return data
        else:
            print(f"Failed to get conversations: {response.text}")
            return []
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return []

def get_documents_by_scenario():
    """Get all documents organized by scenario"""
    print_separator("GETTING DOCUMENTS BY SCENARIO")
    url = f"{API_URL}/documents/by-scenario"
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Count total documents
            total_docs = 0
            for scenario in data:
                total_docs += len(scenario.get("documents", []))
            
            print(f"Found {total_docs} documents across {len(data)} scenarios")
            
            # Extract all document IDs
            all_doc_ids = []
            for scenario in data:
                for doc in scenario.get("documents", []):
                    all_doc_ids.append(doc.get("id"))
            
            return all_doc_ids
        else:
            print(f"Failed to get documents: {response.text}")
            return []
    except Exception as e:
        print(f"Error getting documents: {e}")
        return []

def get_all_documents():
    """Get all documents for the authenticated user"""
    print_separator("GETTING ALL DOCUMENTS")
    url = f"{API_URL}/documents"
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data)} documents")
            
            # Print details of first 3 documents
            for i, doc in enumerate(data[:3]):
                print(f"\nDocument {i+1}:")
                print(f"  ID: {doc.get('id')}")
                print(f"  Title: {doc.get('metadata', {}).get('title')}")
                print(f"  Category: {doc.get('metadata', {}).get('category')}")
                print(f"  Created: {doc.get('metadata', {}).get('created_at')}")
                
            return data
        else:
            print(f"Failed to get documents: {response.text}")
            return []
    except Exception as e:
        print(f"Error getting documents: {e}")
        return []

def test_conversation_bulk_delete(conversation_ids):
    """Test bulk delete for conversations"""
    print_separator(f"TESTING CONVERSATION BULK DELETE WITH {len(conversation_ids)} IDs")
    print(f"Conversation IDs: {conversation_ids}")
    
    url = f"{API_URL}/conversation-history/bulk"
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.delete(url, json=conversation_ids, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"Successfully deleted {data.get('deleted_count')} conversations")
            return True
        else:
            print(f"Failed to delete conversations: {response.text}")
            return False
    except Exception as e:
        print(f"Error deleting conversations: {e}")
        return False

def test_document_bulk_delete(document_ids):
    """Test bulk delete for documents"""
    print_separator(f"TESTING DOCUMENT BULK DELETE WITH {len(document_ids)} IDs")
    print(f"Document IDs: {document_ids}")
    
    url = f"{API_URL}/documents/bulk"
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.delete(url, json=document_ids, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"Successfully deleted {data.get('deleted_count')} documents")
            return True
        else:
            print(f"Failed to delete documents: {response.text}")
            return False
    except Exception as e:
        print(f"Error deleting documents: {e}")
        return False

def test_empty_array_delete():
    """Test bulk delete with empty arrays"""
    print_separator("TESTING BULK DELETE WITH EMPTY ARRAYS")
    
    # Test conversation bulk delete with empty array
    print("\nTesting conversation bulk delete with empty array:")
    url = f"{API_URL}/conversation-history/bulk"
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.delete(url, json=[], headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"Successfully handled empty array for conversations")
        else:
            print(f"Failed to handle empty array for conversations: {response.text}")
    except Exception as e:
        print(f"Error testing empty array for conversations: {e}")
    
    # Test document bulk delete with empty array
    print("\nTesting document bulk delete with empty array:")
    url = f"{API_URL}/documents/bulk"
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.delete(url, json=[], headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"Successfully handled empty array for documents")
        else:
            print(f"Failed to handle empty array for documents: {response.text}")
    except Exception as e:
        print(f"Error testing empty array for documents: {e}")

def main():
    """Main function to run the investigation"""
    print_separator("BULK DELETE INVESTIGATION")
    
    # Login first
    if not login():
        print("Login failed. Cannot proceed with testing.")
        return
    
    # Get conversations
    conversations = get_conversations()
    
    # Get documents by scenario
    document_ids_by_scenario = get_documents_by_scenario()
    
    # Get all documents
    documents = get_all_documents()
    document_ids = [doc.get("id") for doc in documents]
    
    # Test empty array delete
    test_empty_array_delete()
    
    # Test conversation bulk delete with 1 ID if available
    if conversations:
        test_conversation_bulk_delete([conversations[0].get("id")])
    else:
        print("No conversations available for testing")
    
    # Test document bulk delete with 1 ID if available
    if document_ids:
        test_document_bulk_delete([document_ids[0]])
    else:
        print("No documents available for testing")
    
    # Test document bulk delete with IDs from by-scenario endpoint
    if document_ids_by_scenario:
        print("\nTesting document bulk delete with IDs from by-scenario endpoint:")
        test_document_bulk_delete([document_ids_by_scenario[0]])
    else:
        print("No document IDs available from by-scenario endpoint")
    
    # Test with multiple IDs if available
    if len(conversations) >= 2:
        test_conversation_bulk_delete([conv.get("id") for conv in conversations[:2]])
    
    if len(document_ids) >= 2:
        test_document_bulk_delete(document_ids[:2])
    
    print_separator("INVESTIGATION COMPLETE")

if __name__ == "__main__":
    main()
