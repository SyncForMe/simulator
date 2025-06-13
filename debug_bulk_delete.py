#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from dotenv import load_dotenv
import uuid
from pymongo import MongoClient
from bson.objectid import ObjectId
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from frontend/.env and backend/.env
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

logging.info(f"Using MongoDB URL: {MONGO_URL}")
logging.info(f"Using Database: {DB_NAME}")

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

def create_test_documents(num_documents=5):
    """Create test documents for deletion testing"""
    global created_document_ids
    
    if not auth_token:
        if not test_login():
            logging.error("Cannot create test documents without authentication")
            return False
    
    logging.info(f"Creating {num_documents} test documents...")
    
    # Define categories
    categories = ["Protocol", "Training", "Research", "Equipment", "Budget", "Reference"]
    
    # Create documents
    for i in range(num_documents):
        category = categories[i % len(categories)]
        document_data = {
            "title": f"Test {category} Document {uuid.uuid4()}",
            "category": category,
            "description": f"This is a test document for the {category} category",
            "content": f"# Test {category} Document\n\nThis is a test document for the {category} category.",
            "keywords": ["test", category.lower()],
            "authors": ["Test User"]
        }
        
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.post(f"{API_URL}/documents/create", json=document_data, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            document_id = data.get("document_id")
            
            if document_id:
                logging.info(f"Created {category} document with ID: {document_id}")
                created_document_ids.append(document_id)
            else:
                logging.warning(f"Failed to get document ID for {category} document")
        except Exception as e:
            logging.error(f"Failed to create {category} document: {e}")
    
    logging.info(f"Successfully created {len(created_document_ids)} documents")
    return created_document_ids

def verify_documents_in_mongodb(document_ids):
    """Verify documents exist in MongoDB"""
    logging.info(f"Verifying {len(document_ids)} documents in MongoDB...")
    
    # Query MongoDB directly
    documents = list(db.documents.find({"id": {"$in": document_ids}}))
    
    logging.info(f"Found {len(documents)} documents in MongoDB")
    
    # Print document details
    for doc in documents:
        doc_id = doc.get("id")
        metadata = doc.get("metadata", {})
        user_id = metadata.get("user_id", "unknown")
        title = metadata.get("title", "unknown")
        
        logging.info(f"Document ID: {doc_id}")
        logging.info(f"  Title: {title}")
        logging.info(f"  User ID: {user_id}")
        logging.info(f"  MongoDB _id: {doc.get('_id')}")
    
    return documents

def test_post_bulk_delete(document_ids):
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
    
    # Print request details
    logging.info(f"Request URL: {API_URL}/documents/bulk-delete")
    logging.info(f"Request Method: POST")
    logging.info(f"Request Body: {json.dumps(post_data)}")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{API_URL}/documents/bulk-delete", json=post_data, headers=headers)
        
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
            logging.error(f"Bulk delete failed with status code {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error during bulk delete test: {e}")
        return False

def test_delete_bulk_endpoint(document_ids):
    """Test DELETE /api/documents/bulk endpoint"""
    if not auth_token:
        if not test_login():
            logging.error("Cannot test bulk delete without authentication")
            return False
    
    logging.info(f"Testing DELETE /api/documents/bulk with {len(document_ids)} document IDs...")
    
    # Print request details
    logging.info(f"Request URL: {API_URL}/documents/bulk")
    logging.info(f"Request Method: DELETE")
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.delete(f"{API_URL}/documents/bulk", json=document_ids, headers=headers)
        
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
            logging.error(f"Bulk delete failed with status code {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error during bulk delete test: {e}")
        return False

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
    """Main function to test bulk delete functionality"""
    logging.info("Starting bulk delete debug script...")
    
    # Login to get auth token
    if not test_login():
        logging.error("Login failed. Exiting.")
        return
    
    # Create test documents
    document_ids = create_test_documents(10)
    if not document_ids:
        logging.error("Failed to create test documents. Exiting.")
        return
    
    # Verify documents in MongoDB
    documents = verify_documents_in_mongodb(document_ids)
    if not documents:
        logging.error("Failed to verify documents in MongoDB. Exiting.")
        return
    
    # Debug MongoDB query
    debug_mongodb_query(document_ids, test_user_id)
    
    # Test POST bulk delete endpoint
    post_success = test_post_bulk_delete(document_ids)
    
    # Verify documents were deleted
    if post_success:
        deleted = verify_documents_deleted(document_ids)
        if not deleted:
            logging.error("POST bulk delete returned success but documents were not actually deleted!")
        else:
            logging.info("POST bulk delete successfully deleted all documents")
    
    # Create more test documents for DELETE endpoint
    document_ids = create_test_documents(10)
    if not document_ids:
        logging.error("Failed to create test documents for DELETE endpoint. Exiting.")
        return
    
    # Verify documents in MongoDB
    verify_documents_in_mongodb(document_ids)
    
    # Test DELETE bulk endpoint
    delete_success = test_delete_bulk_endpoint(document_ids)
    
    # Verify documents were deleted
    if delete_success:
        deleted = verify_documents_deleted(document_ids)
        if not deleted:
            logging.error("DELETE bulk endpoint returned success but documents were not actually deleted!")
        else:
            logging.info("DELETE bulk endpoint successfully deleted all documents")

if __name__ == "__main__":
    main()
