#!/usr/bin/env python3
import requests
import json
import os
import sys
from dotenv import load_dotenv
import uuid
from pymongo import MongoClient
import logging
import time

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

def test_delete_endpoint(document_ids, method="DELETE", format_type="direct_array"):
    """Test DELETE /api/documents/bulk endpoint with different formats"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test delete without authentication")
            return False, None
    
    endpoint = "/documents/bulk" if method == "DELETE" else "/documents/bulk-delete"
    logging.info(f"Testing {method} {endpoint} with format: {format_type}")
    
    # Prepare request data based on format type
    if format_type == "direct_array":
        data = document_ids
    elif format_type == "document_ids_object":
        data = {"document_ids": document_ids}
    elif format_type == "data_object":
        data = {"data": document_ids}
    else:
        logging.error(f"Unknown format type: {format_type}")
        return False, None
    
    # Print request details
    logging.info(f"Request URL: {API_URL}{endpoint}")
    logging.info(f"Request Method: {method}")
    logging.info(f"Request Body: {json.dumps(data)}")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        if method == "DELETE":
            response = requests.delete(f"{API_URL}{endpoint}", json=data, headers=headers)
        else:  # POST
            response = requests.post(f"{API_URL}{endpoint}", json=data, headers=headers)
        
        logging.info(f"Response Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            logging.info(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            logging.warning(f"Response is not JSON: {response.text}")
            response_data = {}
        
        return response.status_code == 200, response_data
    except Exception as e:
        logging.error(f"Error during delete test: {e}")
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

def debug_mongodb_query(document_ids, user_id):
    """Debug the MongoDB query used for deletion"""
    logging.info("Debugging MongoDB query...")
    
    # Construct the query that would be used for deletion
    query = {
        "id": {"$in": document_ids},
        "metadata.user_id": user_id
    }
    
    logging.info(f"MongoDB query: {query}")
    
    # Execute the query to see what documents would be matched
    documents = list(db.documents.find(query))
    
    logging.info(f"Query would match {len(documents)} documents")
    
    # Check if any documents don't match the query
    all_docs = list(db.documents.find({"id": {"$in": document_ids}}))
    
    if len(all_docs) > len(documents):
        logging.warning(f"Found {len(all_docs)} documents with matching IDs, but only {len(documents)} match the full query")
        
        # Analyze why documents don't match
        for doc in all_docs:
            doc_id = doc.get("id")
            metadata = doc.get("metadata", {})
            doc_user_id = metadata.get("user_id", "unknown")
            
            if doc_user_id != user_id:
                logging.warning(f"Document {doc_id} has user_id '{doc_user_id}' instead of '{user_id}'")
    
    return documents

def main():
    """Main function to compare DELETE and POST endpoints"""
    logging.info("Starting endpoint comparison test...")
    
    # Login to get auth token
    if not test_login():
        logging.error("Login failed. Exiting.")
        return
    
    # Test 1: DELETE endpoint with direct array
    logging.info("\n=== Test 1: DELETE endpoint with direct array ===")
    document_ids = create_test_documents(3)
    if document_ids:
        check_documents_in_mongodb(document_ids)
        debug_mongodb_query(document_ids, test_user_id)
        success, response_data = test_delete_endpoint(document_ids, method="DELETE", format_type="direct_array")
        if success:
            verify_documents_deleted(document_ids)
        else:
            logging.error("DELETE endpoint with direct array failed")
    
    # Test 2: DELETE endpoint with document_ids object
    logging.info("\n=== Test 2: DELETE endpoint with document_ids object ===")
    document_ids = create_test_documents(3)
    if document_ids:
        check_documents_in_mongodb(document_ids)
        debug_mongodb_query(document_ids, test_user_id)
        success, response_data = test_delete_endpoint(document_ids, method="DELETE", format_type="document_ids_object")
        if success:
            verify_documents_deleted(document_ids)
        else:
            logging.error("DELETE endpoint with document_ids object failed")
    
    # Test 3: POST endpoint with document_ids object
    logging.info("\n=== Test 3: POST endpoint with document_ids object ===")
    document_ids = create_test_documents(3)
    if document_ids:
        check_documents_in_mongodb(document_ids)
        debug_mongodb_query(document_ids, test_user_id)
        success, response_data = test_delete_endpoint(document_ids, method="POST", format_type="document_ids_object")
        if success:
            time.sleep(1)  # Wait a moment for deletion to complete
            deleted = verify_documents_deleted(document_ids)
            if not deleted:
                logging.error("POST endpoint returned success but documents were not actually deleted!")
            else:
                logging.info("POST endpoint successfully deleted all documents")
        else:
            logging.error("POST endpoint failed")
    
    # Test 4: Examine MongoDB directly
    logging.info("\n=== Test 4: Examine MongoDB directly ===")
    document_ids = create_test_documents(3)
    if document_ids:
        check_documents_in_mongodb(document_ids)
        debug_mongodb_query(document_ids, test_user_id)
        
        # Try to delete directly from MongoDB
        logging.info("Attempting to delete documents directly from MongoDB...")
        result = db.documents.delete_many({
            "id": {"$in": document_ids},
            "metadata.user_id": test_user_id
        })
        
        logging.info(f"MongoDB delete result: {result.deleted_count} documents deleted")
        
        # Verify deletion
        time.sleep(1)  # Wait a moment for deletion to complete
        verify_documents_deleted(document_ids)
    
    logging.info("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()
