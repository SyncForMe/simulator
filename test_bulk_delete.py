#!/usr/bin/env python3
import requests
import json
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

# Get auth token
def get_auth_token():
    response = requests.post(f"{API_URL}/auth/test-login")
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"Auth token: {token}")
        return token
    else:
        print(f"Failed to get auth token: {response.status_code}")
        return None

# Create a test document
def create_test_document(token):
    headers = {"Authorization": f"Bearer {token}"}
    document_data = {
        "title": f"Test Document for Bulk Delete {uuid.uuid4()}",
        "category": "Protocol",
        "description": "This is a test document for bulk delete testing",
        "content": "# Test Document\n\nThis is a test document for bulk delete testing.",
        "keywords": ["test", "bulk", "delete"],
        "authors": ["Test User"]
    }
    
    response = requests.post(f"{API_URL}/documents/create", json=document_data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        doc_id = data.get("document_id")
        print(f"Created document with ID: {doc_id}")
        return doc_id
    else:
        print(f"Failed to create document: {response.status_code}")
        print(response.text)
        return None

# Test bulk delete with empty array
def test_bulk_delete_empty_array(token):
    print("\n=== Testing bulk delete with empty array ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try with DELETE method
    print("\nTesting DELETE method with empty array:")
    response = requests.delete(f"{API_URL}/documents/bulk", json={"document_ids": []}, headers=headers)
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    # Try with POST method
    print("\nTesting POST method with empty array:")
    response = requests.post(f"{API_URL}/documents/bulk-delete", json={"document_ids": []}, headers=headers)
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# Test bulk delete with valid document IDs
def test_bulk_delete_valid_ids(token, doc_ids):
    print("\n=== Testing bulk delete with valid document IDs ===")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try with DELETE method
    print("\nTesting DELETE method with valid IDs:")
    response = requests.delete(f"{API_URL}/documents/bulk", json={"document_ids": doc_ids}, headers=headers)
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    
    # Try with POST method
    print("\nTesting POST method with valid IDs:")
    response = requests.post(f"{API_URL}/documents/bulk-delete", json={"document_ids": doc_ids}, headers=headers)
    print(f"Status code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

# Main function
def main():
    token = get_auth_token()
    if not token:
        print("Failed to get auth token. Exiting.")
        return
    
    # Test bulk delete with empty array
    test_bulk_delete_empty_array(token)
    
    # Create test documents
    doc_ids = []
    for _ in range(3):
        doc_id = create_test_document(token)
        if doc_id:
            doc_ids.append(doc_id)
    
    if doc_ids:
        # Test bulk delete with valid document IDs
        test_bulk_delete_valid_ids(token, doc_ids)
    else:
        print("No test documents created. Skipping bulk delete test with valid IDs.")

if __name__ == "__main__":
    main()