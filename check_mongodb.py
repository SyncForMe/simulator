#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import logging
import uuid
import requests
import json
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv('/app/backend/.env')
load_dotenv('/app/frontend/.env')

# Get MongoDB connection string
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'ai_simulation')
if not MONGO_URL:
    logging.error("Error: MONGO_URL not found in environment variables")
    exit(1)

# Get the backend URL from environment variables
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL')
if not BACKEND_URL:
    logging.error("Error: REACT_APP_BACKEND_URL not found in environment variables")
    exit(1)

# Ensure the URL ends with /api
API_URL = f"{BACKEND_URL}/api"

# Connect to MongoDB
try:
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    logging.info("Successfully connected to MongoDB")
except Exception as e:
    logging.error(f"Failed to connect to MongoDB: {e}")
    exit(1)

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

def test_bulk_delete_post(document_ids):
    """Test POST /api/documents/bulk-delete endpoint"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test bulk delete without authentication")
            return False
    
    logging.info(f"Testing POST /api/documents/bulk-delete with {len(document_ids)} document IDs...")
    
    # Prepare request data
    post_data = {
        "document_ids": document_ids
    }
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{API_URL}/documents/bulk-delete", json=post_data, headers=headers)
        
        logging.info(f"Response Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            logging.info(f"Response: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200:
                deleted_count = response_data.get("deleted_count", 0)
                logging.info(f"API reports {deleted_count} documents deleted")
                return True
            else:
                logging.error(f"Bulk delete failed with status code {response.status_code}")
                return False
        except json.JSONDecodeError:
            logging.warning(f"Response is not JSON: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error during bulk delete test: {e}")
        return False

def main():
    """Main function to check MongoDB documents"""
    logging.info("Starting MongoDB document check...")
    
    # Login to get auth token
    if not test_login():
        logging.error("Login failed. Exiting.")
        return
    
    # Create test documents
    document_ids = create_test_documents(5)
    if not document_ids:
        logging.error("Failed to create test documents. Exiting.")
        return
    
    # Check documents in MongoDB before deletion
    logging.info("\n=== Documents in MongoDB BEFORE deletion ===")
    found_before = check_documents_in_mongodb(document_ids)
    
    # Test bulk delete
    if found_before:
        logging.info("\n=== Testing bulk delete ===")
        success = test_bulk_delete_post(document_ids)
        
        # Wait a moment for deletion to complete
        time.sleep(1)
        
        # Check documents in MongoDB after deletion
        logging.info("\n=== Documents in MongoDB AFTER deletion ===")
        found_after = check_documents_in_mongodb(document_ids)
        
        # Compare before and after
        if found_after:
            logging.error(f"CRITICAL ISSUE: {len(found_after)} documents still exist in MongoDB after deletion!")
            logging.error(f"Documents not deleted: {found_after}")
        else:
            logging.info("SUCCESS: All documents were properly deleted from MongoDB")
    
    logging.info("\n=== Testing Complete ===")

if __name__ == "__main__":
    main()
