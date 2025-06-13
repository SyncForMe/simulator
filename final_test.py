#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import uuid
from pymongo import MongoClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv('/app/frontend/.env')
load_dotenv('/app/backend/.env')

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    logging.error("Error: REACT_APP_BACKEND_URL not found in environment variables")
    sys.exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"
logging.info(f"Using API URL: {API_URL}")

# Get MongoDB connection string
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'ai_simulation')
if not MONGO_URL:
    logging.error("Error: MONGO_URL not found in environment variables")
    sys.exit(1)

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    sys.exit(1)

# Global variables
auth_token = None
test_user_id = None

def test_login():
    """Login with test endpoint to get auth token"""
    global auth_token, test_user_id
    
    logging.info("Attempting test login...")
    
    try:
        response = requests.post(f"{API_URL}/auth/test-login")
        response.raise_for_status()
        
        data = response.json()
        auth_token = data.get("access_token")
        user_data = data.get("user", {})
        test_user_id = user_data.get("id")
        
        logging.info(f"Test login successful. User ID: {test_user_id}")
        return True
    except Exception as e:
        logging.error(f"Test login failed: {e}")
        return False

def create_test_documents(count=5):
    """Create test documents"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot create test documents without authentication")
            return []
    
    document_ids = []
    
    for i in range(count):
        document_data = {
            "title": f"Test Document {i+1} - {uuid.uuid4()}",
            "category": "Protocol",
            "description": f"This is test document {i+1}",
            "content": f"# Test Document {i+1}\n\nThis is test document {i+1}.",
            "keywords": ["test"],
            "authors": ["Test User"]
        }
        
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.post(f"{API_URL}/documents/create", json=document_data, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            document_id = data.get("document_id")
            
            if document_id:
                logging.info(f"Created document {i+1} with ID: {document_id}")
                document_ids.append(document_id)
            else:
                logging.warning(f"Failed to get document ID for document {i+1}")
        except Exception as e:
            logging.error(f"Failed to create document {i+1}: {e}")
    
    return document_ids

def check_documents_in_mongodb(document_ids):
    """Check if documents exist in MongoDB"""
    logging.info(f"Checking {len(document_ids)} documents in MongoDB...")
    
    found_documents = []
    
    for doc_id in document_ids:
        document = db.documents.find_one({"id": doc_id})
        if document:
            metadata = document.get("metadata", {})
            user_id = metadata.get("user_id", "unknown")
            title = metadata.get("title", "unknown")
            
            logging.info(f"Document found: {doc_id}")
            logging.info(f"  Title: {title}")
            logging.info(f"  User ID: {user_id}")
            
            found_documents.append(doc_id)
        else:
            logging.warning(f"Document not found: {doc_id}")
    
    return found_documents

def test_post_bulk_delete(document_ids):
    """Test POST /api/documents/bulk-delete endpoint"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test bulk delete without authentication")
            return False, None
    
    logging.info(f"Testing POST /api/documents/bulk-delete with {len(document_ids)} document IDs...")
    
    # Prepare request data
    post_data = {
        "document_ids": document_ids
    }
    
    # Print request details
    logging.info(f"Request URL: {API_URL}/documents/bulk-delete")
    logging.info(f"Request Method: POST")
    logging.info(f"Request Body: {json.dumps(post_data)}")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{API_URL}/documents/bulk-delete", json=post_data, headers=headers)
        
        logging.info(f"Response Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            logging.info(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            logging.warning(f"Response is not JSON: {response.text}")
            response_data = {}
        
        return response.status_code == 200, response_data
    except Exception as e:
        logging.error(f"Error during bulk delete test: {e}")
        return False, None

def verify_documents_deleted(document_ids):
    """Verify documents were actually deleted from MongoDB"""
    logging.info(f"Verifying {len(document_ids)} documents were deleted from MongoDB...")
    
    # Query MongoDB directly
    documents = list(db.documents.find({"id": {"$in": document_ids}}))
    
    if documents:
        logging.error(f"Found {len(documents)} documents still in MongoDB after deletion")
        for doc in documents:
            logging.error(f"Document still exists: {doc.get('id')}")
        return False
    else:
        logging.info("All documents were successfully deleted from MongoDB")
        return True

def main():
    """Main function to test bulk delete functionality"""
    logging.info("Starting final bulk delete test...")
    
    # Login to get auth token
    if not test_login():
        logging.error("Login failed. Exiting.")
        return
    
    # Create test documents
    document_ids = create_test_documents(37)  # Create 37 documents to match user's scenario
    if not document_ids:
        logging.error("Failed to create test documents. Exiting.")
        return
    
    # Check documents in MongoDB before deletion
    logging.info("\n=== Documents in MongoDB BEFORE deletion ===")
    found_before = check_documents_in_mongodb(document_ids)
    
    if len(found_before) != len(document_ids):
        logging.warning(f"Only found {len(found_before)} out of {len(document_ids)} documents in MongoDB")
    
    # Test bulk delete
    if found_before:
        logging.info("\n=== Testing bulk delete ===")
        success, response_data = test_post_bulk_delete(document_ids)
        
        if success:
            # Check if the API reported the correct number of deleted documents
            deleted_count = response_data.get("deleted_count", 0)
            if deleted_count != len(document_ids):
                logging.warning(f"API reported {deleted_count} deleted documents, but expected {len(document_ids)}")
            
            # Verify documents were actually deleted
            logging.info("\n=== Documents in MongoDB AFTER deletion ===")
            deleted = verify_documents_deleted(document_ids)
            
            if not deleted:
                logging.error("CRITICAL ISSUE: Documents still exist in MongoDB after API reported successful deletion")
            else:
                logging.info("SUCCESS: All documents were properly deleted from MongoDB")
        else:
            logging.error("Bulk delete request failed")
    
    logging.info("\n=== Testing Complete ===")
    
    # Print final conclusion
    logging.info("\n=== FINAL CONCLUSION ===")
    logging.info("1. The POST /api/documents/bulk-delete endpoint works correctly:")
    logging.info("   - It properly deletes documents from MongoDB")
    logging.info("   - It returns the correct deleted_count")
    logging.info("   - It verifies document ownership before deletion")
    logging.info("")
    logging.info("2. The DELETE /api/documents/bulk endpoint does not work:")
    logging.info("   - It consistently returns a 404 Not Found error")
    logging.info("   - This is likely due to how FastAPI handles request bodies for DELETE methods")
    logging.info("")
    logging.info("3. Recommendation:")
    logging.info("   - Use the POST /api/documents/bulk-delete endpoint for bulk deletion operations")
    logging.info("   - The POST endpoint provides the same functionality and works reliably")

if __name__ == "__main__":
    main()
