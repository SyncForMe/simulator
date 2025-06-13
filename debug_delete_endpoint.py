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
created_document_ids = []

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

def create_test_document():
    """Create a single test document"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot create test document without authentication")
            return None
    
    document_data = {
        "title": f"Test Document {uuid.uuid4()}",
        "category": "Protocol",
        "description": "This is a test document",
        "content": "# Test Document\n\nThis is a test document.",
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
            logging.info(f"Created document with ID: {document_id}")
            return document_id
        else:
            logging.warning("Failed to get document ID")
            return None
    except Exception as e:
        logging.error(f"Failed to create document: {e}")
        return None

def verify_document_in_mongodb(document_id):
    """Verify document exists in MongoDB"""
    document = db.documents.find_one({"id": document_id})
    
    if document:
        metadata = document.get("metadata", {})
        user_id = metadata.get("user_id", "unknown")
        title = metadata.get("title", "unknown")
        
        logging.info(f"Document found in MongoDB:")
        logging.info(f"  ID: {document_id}")
        logging.info(f"  Title: {title}")
        logging.info(f"  User ID: {user_id}")
        logging.info(f"  MongoDB _id: {document.get('_id')}")
        return True
    else:
        logging.error(f"Document not found in MongoDB: {document_id}")
        return False

def test_delete_endpoint_with_format(document_id, format_type):
    """Test DELETE endpoint with different request formats"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test delete without authentication")
            return False
    
    logging.info(f"Testing DELETE /api/documents/bulk with format: {format_type}")
    
    # Prepare request data based on format type
    if format_type == "direct_array":
        data = [document_id]
    elif format_type == "document_ids_object":
        data = {"document_ids": [document_id]}
    elif format_type == "data_object":
        data = {"data": [document_id]}
    else:
        logging.error(f"Unknown format type: {format_type}")
        return False
    
    # Print request details
    logging.info(f"Request URL: {API_URL}/documents/bulk")
    logging.info(f"Request Method: DELETE")
    logging.info(f"Request Body: {json.dumps(data)}")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.delete(f"{API_URL}/documents/bulk", json=data, headers=headers)
        
        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logging.info(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            logging.warning(f"Response is not JSON: {response.text}")
            response_data = {}
        
        if response.status_code == 200:
            deleted_count = response_data.get("deleted_count", 0)
            logging.info(f"Successfully deleted {deleted_count} documents")
            return True
        else:
            logging.error(f"Delete failed with status code {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error during delete test: {e}")
        return False

def verify_document_deleted(document_id):
    """Verify document was actually deleted from MongoDB"""
    document = db.documents.find_one({"id": document_id})
    
    if document:
        logging.error(f"Document still exists in MongoDB after deletion: {document_id}")
        return False
    else:
        logging.info(f"Document was successfully deleted from MongoDB: {document_id}")
        return True

def test_post_delete_endpoint(document_id):
    """Test POST /api/documents/bulk-delete endpoint"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test delete without authentication")
            return False
    
    logging.info(f"Testing POST /api/documents/bulk-delete with document ID: {document_id}")
    
    # Prepare request data
    data = {
        "document_ids": [document_id]
    }
    
    # Print request details
    logging.info(f"Request URL: {API_URL}/documents/bulk-delete")
    logging.info(f"Request Method: POST")
    logging.info(f"Request Body: {json.dumps(data)}")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{API_URL}/documents/bulk-delete", json=data, headers=headers)
        
        logging.info(f"Response Status Code: {response.status_code}")
        logging.info(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            logging.info(f"Response: {json.dumps(response_data, indent=2)}")
        except json.JSONDecodeError:
            logging.warning(f"Response is not JSON: {response.text}")
            response_data = {}
        
        if response.status_code == 200:
            deleted_count = response_data.get("deleted_count", 0)
            logging.info(f"Successfully deleted {deleted_count} documents")
            return True
        else:
            logging.error(f"Delete failed with status code {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error during delete test: {e}")
        return False

def main():
    """Main function to test DELETE endpoint with different formats"""
    logging.info("Starting DELETE endpoint debug script...")
    
    # Login to get auth token
    if not test_login():
        logging.error("Login failed. Exiting.")
        return
    
    # Test format 1: Direct array
    logging.info("\n=== Testing Format 1: Direct Array ===")
    document_id = create_test_document()
    if document_id:
        verify_document_in_mongodb(document_id)
        success = test_delete_endpoint_with_format(document_id, "direct_array")
        if success:
            verify_document_deleted(document_id)
    
    # Test format 2: Object with document_ids field
    logging.info("\n=== Testing Format 2: Object with document_ids field ===")
    document_id = create_test_document()
    if document_id:
        verify_document_in_mongodb(document_id)
        success = test_delete_endpoint_with_format(document_id, "document_ids_object")
        if success:
            verify_document_deleted(document_id)
    
    # Test format 3: Object with data field
    logging.info("\n=== Testing Format 3: Object with data field ===")
    document_id = create_test_document()
    if document_id:
        verify_document_in_mongodb(document_id)
        success = test_delete_endpoint_with_format(document_id, "data_object")
        if success:
            verify_document_deleted(document_id)
    
    # Test POST endpoint for comparison
    logging.info("\n=== Testing POST /api/documents/bulk-delete endpoint ===")
    document_id = create_test_document()
    if document_id:
        verify_document_in_mongodb(document_id)
        success = test_post_delete_endpoint(document_id)
        if success:
            verify_document_deleted(document_id)
    
    logging.info("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()
